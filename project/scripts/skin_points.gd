extends RefCounted
static func evaluate(mesh:MeshInstance3D,skeleton:Skeleton3D)->PackedVector3Array:
	var matrices:Array[Transform3D]=[]
	for i in range(mesh.skin.get_bind_count()):
		var bone:=mesh.skin.get_bind_bone(i)
		if bone<0:bone=skeleton.find_bone(mesh.skin.get_bind_name(i))
		matrices.append(skeleton.global_transform*skeleton.get_bone_global_pose(bone)*mesh.skin.get_bind_pose(i))
	var output:=PackedVector3Array()
	for surface in range(mesh.mesh.get_surface_count()):
		var arrays:=mesh.mesh.surface_get_arrays(surface);var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX];var bones:PackedInt32Array=arrays[Mesh.ARRAY_BONES];var weights:PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
		for i in range(vertices.size()):
			var point:=Vector3.ZERO
			for k in range(4):
				var j:=4*i+k
				if weights[j]>0:point+=(matrices[bones[j]]*vertices[i])*weights[j]
			output.append(point)
	return output
