extends Control
const TRACE=preload("res://scripts/trace.gd")
const SKIN=preload("res://scripts/skin_points.gd")
var report:Dictionary
var players:Array[AnimationPlayer]=[]
var skeletons:Array[Skeleton3D]=[]
var meshes:Array[MeshInstance3D]=[]
var live_delta:=0.
var cameras:Array[Camera3D]=[]
var viewport_boxes:Array[SubViewportContainer]=[]
var page_scroll:ScrollContainer
var timeline:HSlider
var clip_select:OptionButton
var view_select:OptionButton
var speed_select:OptionButton
var status:Label
var key_status:Label
var play_button:Button
var trace:Control
var current_clip:=0
var clock_time:=0.
var playing:=false
var syncing:=false
var failure:=""
func label(text:String,font_size:=16)->Label:
	var l:=Label.new();l.text=text;l.add_theme_font_size_override("font_size",font_size);l.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;l.size_flags_horizontal=Control.SIZE_EXPAND_FILL;return l
func button(text:String,action:Callable)->Button:
	var b:=Button.new();b.text=text;b.custom_minimum_size=Vector2(108,40);b.pressed.connect(action);return b
func _ready()->void:
	report=JSON.parse_string(FileAccess.get_file_as_string("res://comparison.json"))
	var bg:=ColorRect.new();bg.color=Color("142833");bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);add_child(bg)
	page_scroll=ScrollContainer.new();page_scroll.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);page_scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;add_child(page_scroll)
	var margin:=MarginContainer.new();margin.size_flags_horizontal=Control.SIZE_EXPAND_FILL;margin.size_flags_vertical=Control.SIZE_EXPAND_FILL
	for side in ["left","top","right","bottom"]:margin.add_theme_constant_override("margin_"+side,18)
	page_scroll.add_child(margin);var layout:=VBoxContainer.new();layout.add_theme_constant_override("separation",10);margin.add_child(layout)
	layout.add_child(label("Import Lens / optimizer comparison",28))
	layout.add_child(label("Same original GLB, two actual Godot 4.5.1 imports. Only animation optimization differs.",15))
	var controls:=HFlowContainer.new();controls.add_theme_constant_override("h_separation",8);layout.add_child(controls)
	clip_select=OptionButton.new();clip_select.custom_minimum_size=Vector2(180,40);clip_select.add_item("Subtle curved motion");clip_select.add_item("Linear control");clip_select.item_selected.connect(select_clip);controls.add_child(clip_select)
	play_button=button("Play",toggle_play);controls.add_child(play_button);controls.add_child(button("Reset time",reset_time));controls.add_child(button("Largest delta",jump_worst))
	view_select=OptionButton.new();view_select.custom_minimum_size=Vector2(150,40);view_select.add_item("Whole rig");view_select.add_item("Tip close-up");view_select.item_selected.connect(func(_i):update_cameras());controls.add_child(view_select)
	speed_select=OptionButton.new();speed_select.custom_minimum_size=Vector2(100,40);speed_select.add_item("1× speed");speed_select.add_item("0.25× speed");controls.add_child(speed_select)
	var views:=HBoxContainer.new();views.add_theme_constant_override("separation",12);views.size_flags_vertical=Control.SIZE_EXPAND_FILL;layout.add_child(views)
	for side in ["default","optimizer_off"]:
		var column:=VBoxContainer.new();column.size_flags_horizontal=Control.SIZE_EXPAND_FILL;column.size_flags_vertical=Control.SIZE_EXPAND_FILL;views.add_child(column)
		column.add_child(label("Default optimizer" if side=="default" else "Optimizer disabled",18))
		var box:=SubViewportContainer.new();box.stretch=true;box.size_flags_horizontal=Control.SIZE_EXPAND_FILL;box.size_flags_vertical=Control.SIZE_EXPAND_FILL;box.custom_minimum_size=Vector2(40,180);column.add_child(box);viewport_boxes.append(box)
		var viewport:=SubViewport.new();viewport.own_world_3d=true;viewport.size=Vector2i(500,380);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;box.add_child(viewport)
		var scene:=Node3D.new();viewport.add_child(scene)
		var packed:=load("res://models/"+side+"/IL_Antenna.glb") as PackedScene
		if packed==null:failure="Could not load included calibration model.";continue
		var model:=packed.instantiate();scene.add_child(model)
		var ps:=model.find_children("*","AnimationPlayer",true,false);var ss:=model.find_children("*","Skeleton3D",true,false)
		if ps.size()!=1 or ss.size()!=1:failure="Unexpected calibration hierarchy.";continue
		var player:=ps[0] as AnimationPlayer;player.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL;players.append(player);skeletons.append(ss[0]);meshes.append(model.find_children("*","MeshInstance3D",true,false)[0])
		var environment:=WorldEnvironment.new();var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color("e9e6db");env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color("ffffff");env.ambient_light_energy=.65;env.tonemap_mode=Environment.TONE_MAPPER_LINEAR;environment.environment=env;scene.add_child(environment)
		var light:=DirectionalLight3D.new();light.rotation_degrees=Vector3(-35,-35,0);light.light_energy=1.5;scene.add_child(light)
		var fill:=DirectionalLight3D.new();fill.rotation_degrees=Vector3(-20,140,0);fill.light_energy=.5;scene.add_child(fill)
		var camera:=Camera3D.new();camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.current=true;scene.add_child(camera);cameras.append(camera)
		var ground:=MeshInstance3D.new();var plane:=PlaneMesh.new();plane.size=Vector2(3,3);ground.mesh=plane;var mat:=StandardMaterial3D.new();mat.albedo_color=Color("ccd1c5");mat.roughness=.85;ground.material_override=mat;ground.position.y=-.003;scene.add_child(ground)
	key_status=label("",14);layout.add_child(key_status)
	timeline=HSlider.new();timeline.max_value=4.;timeline.step=1./60.;timeline.custom_minimum_size.y=28;timeline.value_changed.connect(func(value):if not syncing:playing=false;set_time(value));layout.add_child(timeline)
	status=label("",16);layout.add_child(status)
	layout.add_child(label("Maximum sampled mesh displacement between imports (mm)",14))
	trace=TRACE.new();trace.custom_minimum_size.y=110;layout.add_child(trace)
	layout.add_child(label("A difference is not automatically a defect. Disabled optimization is a comparison baseline. This calibration was modeled in metres; the trace uses CPU-skinned imported vertices.",13))
	if failure!="":status.text=failure;set_process(false);return
	select_clip(0);update_cameras()
func select_clip(index:int)->void:
	current_clip=index;playing=false
	if clip_select.selected!=index:clip_select.select(index)
	var data:Dictionary=report.clips[index]
	for p in players:
		p.stop();p.get_animation(data.clip).loop_mode=Animation.LOOP_NONE;p.play(data.clip,0.);p.advance(0.)
	trace.values=data.per_time_max_file_units;trace.queue_redraw()
	var a:=0;var b:=0
	for t in data.default_tracks:a+=t.keys
	for t in data.optimizer_off_tracks:b+=t.keys
	key_status.text="Animation keys: %d / %d  ·  Largest measured difference: %.6f mm at %.3f s"%[a,b,float(data.max_displacement_file_units)*1000.,data.worst_time_seconds]
	set_time(0.)
func set_time(value:float)->void:
	clock_time=clampf(value,0.,4.)
	for i in range(players.size()):players[i].seek(clock_time,true);skeletons[i].force_update_all_bone_transforms()
	syncing=true;timeline.value=clock_time;syncing=false
	var data:Dictionary=report.clips[current_clip];var index:=clampi(roundi(clock_time*60),0,data.per_time_max_file_units.size()-1)
	var left:PackedVector3Array=SKIN.evaluate(meshes[0],skeletons[0]);var right:PackedVector3Array=SKIN.evaluate(meshes[1],skeletons[1]);live_delta=0.
	for v in range(left.size()):live_delta=maxf(live_delta,left[v].distance_to(right[v]))
	status.text="%.3f / 4.000 s  ·  live CPU delta: %.6f mm  ·  nearest recorded sample: %.6f mm"%[clock_time,live_delta*1000.,float(data.per_time_max_file_units[index])*1000.]
	play_button.text="Pause" if playing else "Play";trace.cursor=clock_time;trace.queue_redraw()
func toggle_play()->void:
	playing=not playing
	if playing and clock_time>=4.:set_time(0.)
	play_button.text="Pause" if playing else "Play"
func reset_time()->void:playing=false;set_time(0.)
func jump_worst()->void:playing=false;set_time(report.clips[current_clip].worst_time_seconds)
func update_cameras()->void:
	for camera in cameras:
		var close:=view_select.selected==1;var target:=Vector3(.06,1.19,0) if close else Vector3(0,.62,0)
		camera.size=.32 if close else 1.5;camera.position=target+Vector3(0,0,3);camera.look_at(target)
func _process(delta:float)->void:
	if playing and is_visible_in_tree():
		var speed:=1. if speed_select.selected==0 else .25
		set_time(fmod(clock_time+delta*speed,4.))
