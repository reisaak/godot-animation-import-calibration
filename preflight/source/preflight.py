"""Strict offline preflight for the limited Import Lens GLB intake prototype."""
import json, struct, math
class Rejected(Exception):
 def __init__(self,reason,kind='UNSUPPORTED'):
  super().__init__(reason);self.reason=reason;self.kind=kind

def fail(reason,kind='MALFORMED'):raise Rejected(reason,kind)
def integer(v):return type(v) is int
def require(ok,reason,kind='MALFORMED'):
 if not ok:fail(reason,kind)
def parse(blob):
 require(20<=len(blob)<=25*1024*1024,'Expected a GLB between 20 bytes and 25 MiB.')
 magic,version,length=struct.unpack_from('<4sII',blob)
 require(magic==b'glTF' and version==2 and length==len(blob),'Invalid GLB 2 header or declared length.')
 chunks=[];pos=12
 while pos<len(blob):
  require(pos+8<=len(blob),'Truncated GLB chunk header.');size,kind=struct.unpack_from('<II',blob,pos);pos+=8
  require(size%4==0 and pos+size<=len(blob),'Truncated or unaligned GLB chunk.');chunks.append((kind,blob[pos:pos+size]));pos+=size
 require(len(chunks)==2 and chunks[0][0]==0x4e4f534a and chunks[1][0]==0x004e4942,'Exactly one JSON chunk and one embedded BIN chunk are supported.','UNSUPPORTED')
 try:g=json.loads(chunks[0][1].decode('utf-8'))
 except (ValueError,UnicodeError):fail('GLB JSON is invalid.')
 require(isinstance(g,dict) and g.get('asset',{}).get('version')=='2.0','Expected a glTF 2.0 asset.')
 require(not g.get('extensionsUsed') and not g.get('extensionsRequired'),'Extensions are not supported by this calibration intake.','UNSUPPORTED')
 def scan(v):
  if isinstance(v,dict):
   require(not v.get('extensions'),'Extension payloads are unsupported.','UNSUPPORTED')
   require('uri' not in v,'External files and URI/data-URI resources are unsupported. Use an embedded self-contained GLB.','UNSUPPORTED')
   for value in v.values():scan(value)
  elif isinstance(v,list):
   for value in v:scan(value)
  elif isinstance(v,float):require(math.isfinite(v),'Non-finite JSON number.')
 scan(g)
 buffers=g.get('buffers',[]);require(len(buffers)==1,'Exactly one embedded buffer is supported.','UNSUPPORTED')
 declared=buffers[0].get('byteLength');binary=chunks[1][1]
 require(integer(declared) and 0<=len(binary)-declared<=3,'Invalid embedded buffer byteLength.')
 views=g.get('bufferViews',[]);accessors=g.get('accessors',[])
 for v in views:
  require(v.get('buffer')==0,'Invalid buffer reference.');off=v.get('byteOffset',0);size=v.get('byteLength')
  require(integer(off) and integer(size) and off>=0 and size>=0 and off+size<=declared,'Buffer view exceeds the embedded buffer.')
 def indexed(items,i,label):
  require(integer(i) and 0<=i<len(items),'Invalid '+label+' index.');return items[i]
 formats={5120:('b',1),5121:('B',1),5122:('h',2),5123:('H',2),5125:('I',4),5126:('f',4)};widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
 cache={}
 def read(i):
  a=indexed(accessors,i,'accessor')
  if i in cache:return cache[i]
  require('sparse' not in a,'Sparse accessors are unsupported.','UNSUPPORTED');require(a.get('componentType') in formats and a.get('type') in widths,'Unsupported accessor representation.','UNSUPPORTED')
  v=indexed(views,a.get('bufferView'),'buffer view');code,unit=formats[a['componentType']];width=widths[a['type']];count=a.get('count');off=a.get('byteOffset',0);stride=v.get('byteStride',unit*width)
  require(integer(count) and 0<count<=2000000 and integer(off) and off>=0 and integer(stride) and stride>=unit*width and stride%unit==0,'Invalid accessor layout or count.')
  require(off+(count-1)*stride+unit*width<=v['byteLength'],'Accessor exceeds its buffer view.')
  values=[struct.unpack_from('<'+code*width,binary,v.get('byteOffset',0)+off+n*stride) for n in range(count)]
  require(all(math.isfinite(x) for row in values for x in row),'Non-finite accessor values.')
  cache[i]=values;return values
 for i in range(len(accessors)):read(i)
 nodes=g.get('nodes',[]);require(isinstance(nodes,list) and 1<=len(nodes)<=256,'At most 256 nodes are supported.','UNSUPPORTED')
 parents={}
 for ni,n in enumerate(nodes):
  for child in n.get('children',[]):
   indexed(nodes,child,'node');require(child not in parents,'Node has multiple parents.');parents[child]=ni
  for field,length in [('translation',3),('rotation',4),('scale',3),('matrix',16)]:
   if field in n:require(isinstance(n[field],list) and len(n[field])==length and all(type(x) in (int,float) and math.isfinite(x) for x in n[field]),'Invalid node '+field+'.')
  require(not ('matrix' in n and any(k in n for k in ['translation','rotation','scale'])),'Node mixes matrix and TRS.')
  if 'rotation' in n:require(abs(sum(x*x for x in n['rotation'])-1)<1e-3,'Node quaternion is not unit length.')
  if 'scale' in n:require(all(abs(x)>1e-8 for x in n['scale']),'Zero-scale node is unsupported.','UNSUPPORTED')
 for start in range(len(nodes)):
  seen=set();cur=start
  while cur in parents:
   require(cur not in seen,'Node cycle.');seen.add(cur);cur=parents[cur]
 scenes=g.get('scenes',[]);require(len(scenes)==1 and g.get('scene',0)==0,'Exactly one scene is supported.','UNSUPPORTED')
 for node in scenes[0].get('nodes',[]):indexed(nodes,node,'scene node');require(node not in parents,'Scene root is also a child.')
 skins=g.get('skins',[]);meshes=g.get('meshes',[])
 require(len(skins)==1 and len(meshes)==1,'Exactly one skin and one mesh are supported.','UNSUPPORTED')
 mesh_nodes=[(i,n) for i,n in enumerate(nodes) if 'mesh' in n]
 require(len(mesh_nodes)==1 and mesh_nodes[0][1].get('mesh')==0 and mesh_nodes[0][1].get('skin')==0,'Exactly one skinned mesh instance using the only skin is supported.','UNSUPPORTED')
 joints=skins[0].get('joints',[]);require(1<=len(joints)<=64 and len(set(joints))==len(joints),'Skin must have 1–64 unique joints.','UNSUPPORTED')
 for j in joints:indexed(nodes,j,'joint')
 require('inverseBindMatrices' in skins[0],'Explicit inverse bind matrices are required.','UNSUPPORTED')
 ib=skins[0]['inverseBindMatrices'];require(accessors[ib].get('type')=='MAT4' and accessors[ib].get('componentType')==5126 and len(read(ib))==len(joints),'Inverse bind matrix count/type mismatch.')
 total=0
 for p in meshes[0].get('primitives',[]):
  require(p.get('mode',4)==4,'Only triangle primitives are supported.','UNSUPPORTED');require(not p.get('targets') and not meshes[0].get('weights'),'Morph targets are unsupported.','UNSUPPORTED')
  attrs=p.get('attributes',{});require(all(x in attrs for x in ['POSITION','JOINTS_0','WEIGHTS_0']),'Every primitive must have positions and four-slot skin data.','UNSUPPORTED');require('JOINTS_1' not in attrs and 'WEIGHTS_1' not in attrs,'More than four influences are unsupported.','UNSUPPORTED')
  pos=read(attrs['POSITION']);js=read(attrs['JOINTS_0']);ws=read(attrs['WEIGHTS_0']);total+=len(pos)
  require(accessors[attrs['POSITION']]['type']=='VEC3' and accessors[attrs['POSITION']]['componentType']==5126,'Positions must be float VEC3.')
  require(accessors[attrs['JOINTS_0']]['type']=='VEC4' and accessors[attrs['JOINTS_0']]['componentType'] in (5121,5123),'Joints must be unsigned VEC4.')
  require(accessors[attrs['WEIGHTS_0']]['type']=='VEC4' and accessors[attrs['WEIGHTS_0']]['componentType']==5126,'This prototype accepts float VEC4 weights only.','UNSUPPORTED')
  require(len(pos)==len(js)==len(ws),'Skin attribute counts differ.')
  require(all(0<=j<len(joints) for row in js for j in row),'Joint reference outside skin.')
  require(all(all(0<=w<=1 for w in row) and abs(sum(row)-1)<1e-3 for row in ws),'Invalid source skin weights.')
  if 'indices' in p:
   a=accessors[p['indices']];ix=read(p['indices']);require(a['type']=='SCALAR' and a['componentType'] in (5121,5123,5125) and len(ix)%3==0 and all(0<=x[0]<len(pos) for x in ix),'Invalid triangle indices.')
  else:require(len(pos)%3==0,'Unindexed triangle count is not divisible by three.')
 require(1<=total<=20000,'At most 20,000 source split vertices are supported.','UNSUPPORTED')
 for image in g.get('images',[]):
  require(image.get('mimeType') in ('image/png','image/jpeg') and 'bufferView' in image,'Only embedded PNG/JPEG images are supported.','UNSUPPORTED');indexed(views,image['bufferView'],'image buffer view')
 animations=g.get('animations',[]);require(1<=len(animations)<=8,'One to eight animations are supported.','UNSUPPORTED');clip_info=[];names=set()
 for animation in animations:
  name=animation.get('name');require(isinstance(name,str) and name and name not in names and all(c.isalnum() or c in '_- ' for c in name),'Clips need unique simple names (letters, digits, spaces, hyphens, underscores).','UNSUPPORTED');names.add(name)
  samplers=animation.get('samplers',[]);targets=set();end=0.
  for channel in animation.get('channels',[]):
   target=channel.get('target',{});node=target.get('node');path=target.get('path');require(node in joints and path in ('translation','rotation','scale'),'Only joint translation/rotation/scale animation is supported.','UNSUPPORTED');require((node,path) not in targets,'Duplicate animation target channel.');targets.add((node,path))
   sampler=indexed(samplers,channel.get('sampler'),'sampler');require(sampler.get('interpolation','LINEAR') in ('LINEAR','STEP'),'Only LINEAR/STEP animation interpolation is supported.','UNSUPPORTED');ti=sampler.get('input');oi=sampler.get('output');times=read(ti);values=read(oi)
   require(accessors[ti]['type']=='SCALAR' and accessors[ti]['componentType']==5126,'Animation time must be float scalar.')
   require(times[0][0]>=0 and all(b[0]>a[0] for a,b in zip(times,times[1:])),'Animation times must increase from a nonnegative value.')
   require(len(times)==len(values) and accessors[oi]['componentType']==5126 and accessors[oi]['type']==('VEC4' if path=='rotation' else 'VEC3'),'Animation output type/count mismatch.')
   if path=='rotation':require(all(abs(sum(x*x for x in row)-1)<1e-3 for row in values),'Animation quaternion is not unit length.')
   end=max(end,times[-1][0])
  require(targets and 0<end<=30,'Animation needs channels and a duration up to 30 seconds.','UNSUPPORTED');clip_info.append({'name':name,'end_seconds':end,'channels':len(targets)})
 return {'version':'2.0','source_split_vertices':total,'joint_count':len(joints),'clips':clip_info,'self_contained':True,'one_mesh_one_skin':True,'extensions':False,'buffer_bytes':declared}
