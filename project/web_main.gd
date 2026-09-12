extends Control
const INSPECTOR = preload("res://main.tscn")
var inspector:Control
func _ready()->void:
	var area:=MarginContainer.new()
	area.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	area.add_theme_constant_override("margin_top",52)
	add_child(area)
	inspector=INSPECTOR.instantiate()
	inspector.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	inspector.size_flags_vertical=Control.SIZE_EXPAND_FILL
	area.add_child(inspector)

# Reserved Web-wrapper shortcut: leave the inspector's ordinary keys untouched.
func _unhandled_key_input(event:InputEvent)->void:
	if not event is InputEventKey or not event.pressed:
		return
	if not event.alt_pressed or event.ctrl_pressed or event.meta_pressed or event.shift_pressed:
		return
	if event.keycode != KEY_PAGEDOWN and event.keycode != KEY_PAGEUP:
		return
	if not is_instance_valid(inspector) or not is_instance_valid(inspector.page_scroll):
		return
	var scroll:ScrollContainer=inspector.page_scroll
	var step:=maxi(1,roundi(scroll.size.y*.8))
	scroll.scroll_vertical += step if event.keycode == KEY_PAGEDOWN else -step
	get_viewport().set_input_as_handled()
