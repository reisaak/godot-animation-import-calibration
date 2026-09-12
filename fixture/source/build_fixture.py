"""Original Import Lens analytical calibration rig. Blender 4.5.13; no external assets."""
from pathlib import Path
import bpy,bmesh,math,json,hashlib,struct
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.name='Import_Lens_Calibration';s.render.fps=30;s.frame_start=1;s.frame_end=121
s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
mats=[]
for name,col in [('Base','253f50'),('Stem','329b92'),('Bands','aed7ce'),('Tip','e9ae42')]:
 rgb=[int(col[k:k+2],16)/255 for k in (0,2,4)];linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
 m=bpy.data.materials.new('IL_'+name);m.diffuse_color=(*linear,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=.65;mats.append(m)
verts=[];faces=[];materials=[];weights=[]
def vert(v,w):
 i=len(verts);verts.append(tuple(v));weights.append(w);return i
def face(v,m):faces.append(v);materials.append(m)
def skin(z):
 if z<=.16:return {'Root':1}
 if z<.28:
  a=(z-.16)/.12;return {'Root':1-a,'Lower':a}
 if z<=.51:return {'Lower':1}
 if z<.78:
  a=(z-.51)/.27;return {'Lower':1-a,'Upper':a}
 return {'Upper':1}
def ring(z,r,n=12):return [vert((math.cos(i*2*math.pi/n)*r,math.sin(i*2*math.pi/n)*r,z),skin(z)) for i in range(n)]
def connect(a,b,m):
 for i in range(len(a)):face([a[i],a[(i+1)%len(a)],b[(i+1)%len(a)],b[i]],m)
# Original bevel-stepped pedestal, all root weighted.
rings=[]
for z,r in [(0,.19),(.022,.215),(.12,.215),(.145,.185)]:rings.append(ring(z,r))
face(list(reversed(rings[0])),0)
for a,b in zip(rings,rings[1:]):connect(a,b,0)
face(rings[-1],0)
# Densely segmented stem: blended weights visibly bend, not just rigid rocking.
rings=[]
for i in range(25):
 z=.145+i/24*1.02;r=.042-(z-.145)*.018;rings.append(ring(z,r,10))
face(list(reversed(rings[0])),1)
for i,(a,b) in enumerate(zip(rings,rings[1:])):connect(a,b,2 if i in (4,12,20) else 1)
face(rings[-1],1)
# Solid rounded signal cap, all upper-bone weighted.
rings=[]
for z,r in [(1.145,.022),(1.16,.068),(1.19,.082),(1.23,.068),(1.245,.022)]:rings.append(ring(z,r))
face(list(reversed(rings[0])),3)
for a,b in zip(rings,rings[1:]):connect(a,b,3)
face(rings[-1],3)
arm=bpy.data.armatures.new('IL_Skeleton');rig=bpy.data.objects.new('IL_Antenna_Rig',arm);s.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
prev=None
for name,head,tail in [('Root',(0,0,0),(0,0,.15)),('Lower',(0,0,.15),(0,0,.65)),('Upper',(0,0,.65),(0,0,1.25))]:
 b=arm.edit_bones.new(name);b.head=head;b.tail=tail;b.parent=prev;b.use_connect=prev is not None;prev=b
bpy.ops.object.mode_set(mode='OBJECT');arm.display_type='STICK';rig.show_in_front=True
mesh=bpy.data.meshes.new('IL_Antenna_Geometry');mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new('IL_Antenna_Mesh',mesh);s.collection.objects.link(obj)
for m in mats:mesh.materials.append(m)
for p,mi in zip(mesh.polygons,materials):p.material_index=mi
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
for name in ['Root','Lower','Upper']:obj.vertex_groups.new(name=name)
for i,w in enumerate(weights):
 for name,v in w.items():
  if v:obj.vertex_groups[name].add([i],v,'REPLACE')
mod=obj.modifiers.new('IL_Analytical_Skin','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=False;obj.parent=rig
rig['provenance']='Original analytical calibration geometry/rig/code, AI-assisted development. Not a plant or character asset.'
rig.animation_data_create()
def angles(clip,t):
 if clip=='LinearControl':return (.04*t,0.0)
 w=2*math.pi*t/4;return (.085*(math.sin(w)+.08*math.sin(5*w)),.055*(math.sin(w)+.14*math.sin(3*w)))
for clip in ['SubtleCurve','LinearControl']:
 rig.animation_data.action=None
 for frame in range(1,122):
  t=(frame-1)/30;a,b=angles(clip,t)
  for name,value in [('Root',0.),('Lower',a),('Upper',b)]:
   pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION';axis=arm.bones[name].matrix_local.to_quaternion().inverted() @ Vector((0,1,0));pb.rotation_quaternion=Quaternion(axis,value);pb.keyframe_insert('rotation_quaternion',frame=frame,group=name)
 action=rig.animation_data.action;action.name=clip
 for slot in action.slots:
  for layer in action.layers:
   for strip in layer.strips:
    bag=strip.channelbag(slot)
    if bag:
     for fc in bag.fcurves:
      for k in fc.keyframe_points:k.interpolation='LINEAR'
 track=rig.animation_data.nla_tracks.new();track.name=clip;strip=track.strips.new(clip,1,action);strip.action_frame_start=1;strip.action_frame_end=121
rig.animation_data.action=None
for t in rig.animation_data.nla_tracks:t.mute=False
s.frame_set(1)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);obj.select_set(True);bpy.context.view_layer.objects.active=rig
path=R/'models/IL_Antenna.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_frame_range=False,export_anim_slide_to_zero=True,export_force_sampling=True,export_extras=False,export_cameras=False,export_lights=False,export_skins=True)
# Authoritative saved source opens with only the subtle clip active.
for t in rig.animation_data.nla_tracks:t.mute=t.name!='SubtleCurve'
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(R/'IL_Calibration.blend'))
mesh.calc_loop_triangles();binary=path.read_bytes();g=json.loads(binary[20:20+struct.unpack_from('<I',binary,12)[0]])
info={'status':'Original prototype calibration only; no general buyer intake','blender':bpy.app.version_string,'glb_sha256':hashlib.sha256(binary).hexdigest(),'source_vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),'bones':['Root','Lower','Upper'],'materials':len(mats),'animations':[a.get('name') for a in g['animations']],'fps':30,'duration_seconds':4,'source_frame_end_inclusive':121,'rotation_axis_blender_world':[0,1,0],'pivot_lower_blender':[0,0,.15],'pivot_upper_blender':[0,0,.65],'source_positions_blender':verts,'source_weights':weights,'clip_formula':{'LinearControl':'lower=.04*t; upper=0','SubtleCurve':'w=2*pi*t/4; lower=.085*(sin(w)+.08*sin(5*w)); upper=.055*(sin(w)+.14*sin(3*w))'},'interpolation':'sampled at30Hz, quaternion glTF LINEAR; same-axis intervals equal linearly interpolated angles','coordinate_conversion':'Blender(x,y,z) to glTF/Godot(x,z,-y)','source_owns':{'geometry':True,'rig':True,'animations':True,'no_paid_plant_geometry':True}}
(R/'fixture.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps({k:v for k,v in info.items() if k not in ['source_positions_blender','source_weights']},indent=2))
