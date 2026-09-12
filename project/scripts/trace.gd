extends Control
var values:Array=[]
var duration:=4.
var cursor:=0.
func _draw() -> void:
	var chart:=Rect2(44,12,max(20,size.x-62),max(20,size.y-36))
	draw_style_box(panel(),Rect2(Vector2.ZERO,size))
	for level in [0.,1.,2.]:
		var y:float=chart.end.y-float(level)/2.*chart.size.y
		draw_line(Vector2(chart.position.x,y),Vector2(chart.end.x,y),Color("3b505b"),1)
		draw_string(ThemeDB.fallback_font,Vector2(8,y+4),"%.0f"%float(level),HORIZONTAL_ALIGNMENT_LEFT,-1,13,Color("d7e2e5"))
	if values.size()>1:
		var points:=PackedVector2Array()
		for i in range(values.size()):points.append(Vector2(chart.position.x+chart.size.x*i/(values.size()-1),chart.end.y-min(2.,float(values[i])*1000.)/2.*chart.size.y))
		draw_polyline(points,Color("eab64d"),2,true)
	var x:=chart.position.x+chart.size.x*cursor/duration;draw_line(Vector2(x,chart.position.y),Vector2(x,chart.end.y),Color("f4f5ee"),1)
	draw_string(ThemeDB.fallback_font,Vector2(chart.position.x,size.y-7),"0 s",HORIZONTAL_ALIGNMENT_LEFT,-1,13,Color("d7e2e5"))
	draw_string(ThemeDB.fallback_font,Vector2(chart.end.x-30,size.y-7),"4 s",HORIZONTAL_ALIGNMENT_LEFT,-1,13,Color("d7e2e5"))
func panel()->StyleBoxFlat:
	var p:=StyleBoxFlat.new();p.bg_color=Color("20343f");p.corner_radius_top_left=8;p.corner_radius_top_right=8;p.corner_radius_bottom_left=8;p.corner_radius_bottom_right=8;return p
