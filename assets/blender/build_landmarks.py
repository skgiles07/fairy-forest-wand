"""Create Heartlight Quest's original, editable three-landmark collection.

Send this source to the local Blender MCP execute_blender_code tool.
It creates a NEW scene and writes only the project's named generated outputs.
No external textures, downloads, paid services, or existing-object deletion.
"""
import bpy
import math
import random
import json
from mathutils import Vector

OUTPUT = '/Users/scottgiles/Projects/fairy-forest-wand/hub/static/assets/models/'
BLEND = '/Users/scottgiles/Projects/fairy-forest-wand/assets/blender/heartlight-landmarks.blend'
PREVIEW = '/Users/scottgiles/Projects/fairy-forest-wand/assets/blender/heartlight-landmarks-preview.png'
random.seed(31)
scene = bpy.data.scenes.new('Heartlight • Three Household Landmarks')
bpy.context.window.scene = scene
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 97
scene.render.resolution_x = 960
scene.render.resolution_y = 540
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except (TypeError, ValueError):
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
scene.world = bpy.data.worlds.new('Heartlight • Midnight woodland studio')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.027, 0.052, 0.10, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.45
try:
    scene.view_settings.view_transform = 'AgX'
except (TypeError, ValueError):
    pass


def material(name, color, metallic=0, roughness=0.4, emission=0):
    mat = bpy.data.materials.new('Heartlight • ' + name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*color, 1)
        bsdf.inputs['Emission Strength'].default_value = emission
    mat.diffuse_color = (*color, 1)
    return mat


moss = material('Deep velvet moss', (0.055, 0.20, 0.125), roughness=0.7)
moss_light = material('Moss tips', (0.16, 0.38, 0.21), roughness=0.66)
stone = material('Blue slate', (0.08, 0.15, 0.23), metallic=0.08, roughness=0.5)
gold = material('Brushed old brass', (0.64, 0.40, 0.12), metallic=0.8, roughness=0.27)
gold_light = material('Polished brass edge', (0.94, 0.70, 0.30), metallic=0.7, roughness=0.2)
wood = material('Elder heartwood', (0.17, 0.069, 0.032), roughness=0.5)
wood_light = material('Warm cut wood', (0.32, 0.13, 0.044), roughness=0.43)
wood_dark = material('Carved bark grooves', (0.065, 0.025, 0.018), roughness=0.64)
chest_wood = material('Chest amber oak', (0.38, 0.16, 0.047), roughness=0.3)
chest_alt = material('Chest honey grain', (0.53, 0.27, 0.084), roughness=0.31)
leaf_a = material('Canopy emerald', (0.035, 0.28, 0.18), roughness=0.33)
leaf_b = material('Canopy jade', (0.10, 0.43, 0.25), roughness=0.32)
leaf_c = material('Canopy young leaves', (0.32, 0.57, 0.28), roughness=0.37)
lilac = material('Enchanted lilac', (0.55, 0.28, 0.92), metallic=0.17, roughness=0.18, emission=0.45)
cyan = material('Moon crystal cyan', (0.18, 0.80, 0.94), metallic=0.23, roughness=0.15, emission=0.25)
cyan_dark = material('Moon crystal deep facet', (0.13, 0.34, 0.67), metallic=0.26, roughness=0.18)
moon_white = material('Crystal light facet', (0.60, 0.93, 1.0), metallic=0.18, roughness=0.13, emission=0.35)
glow = material('Heartlight glow', (0.36, 0.92, 0.96), roughness=0.2, emission=2.6)
lilac_glow = material('Firefly lilac glow', (0.67, 0.34, 0.96), roughness=0.2, emission=2)
inside = material('Chest blue velvet', (0.014, 0.08, 0.12), roughness=0.76)

assets = []


def asset(name):
    collection = bpy.data.collections.new('Heartlight • ' + name)
    scene.collection.children.link(collection)
    root = bpy.data.objects.new(name, None)
    collection.objects.link(root)
    root.empty_display_type = 'PLAIN_AXES'
    root['landmark'] = name
    root['authored_for'] = 'Liza’s Heartlight Quest'
    assets.append((name, collection, root))
    return collection, root


def add(obj, name, collection, parent=None, mat=None):
    obj.name = name
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)
    if parent:
        obj.parent = parent
    if mat:
        obj.data.materials.append(mat)
    return obj


def mesh(name, verts, faces, collection, parent, mat):
    data = bpy.data.meshes.new(name + ' geometry')
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.parent = parent
    if mat:
        data.materials.append(mat)
    return obj


def smooth(obj):
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def sphere(name, location, scale, collection, parent, mat, subdivision=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivision, radius=1)
    obj = add(bpy.context.object, name, collection, parent, mat)
    obj.location = location
    obj.scale = scale
    return smooth(obj)


def cube(name, location, dimensions, collection, parent, mat, bevel=0.035):
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = add(bpy.context.object, name, collection, parent, mat)
    obj.location = location
    obj.dimensions = dimensions
    # Apply dimensions to this newly generated object only, so bevel is even.
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new('Soft hand-carved edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
    return obj


def cylinder(name, location, radius, depth, collection, parent, mat, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth)
    obj = add(bpy.context.object, name, collection, parent, mat)
    obj.location = location
    return obj


def ring(name, location, major, minor, collection, parent, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_segments=40, minor_segments=6, major_radius=major, minor_radius=minor)
    obj = add(bpy.context.object, name, collection, parent, mat)
    obj.location = location
    obj.rotation_euler = rotation
    return smooth(obj)


def tube(name, points, radius, collection, parent, mat, sides=7):
    # Explicit mesh tubes export consistently without relying on curve conversion.
    verts = []
    for i, point in enumerate(points):
        center = Vector(point[:3])
        direction = Vector(points[min(i + 1, len(points)-1)][:3]) - Vector(points[max(i - 1, 0)][:3])
        if direction.length < 0.001:
            direction = Vector((0, 0, 1))
        direction.normalize()
        across = direction.cross(Vector((0, 0, 1)))
        if across.length < 0.01:
            across = direction.cross(Vector((0, 1, 0)))
        across.normalize()
        along = direction.cross(across).normalized()
        r = point[3] if len(point) > 3 else radius
        for j in range(sides):
            theta = j * math.tau / sides
            verts.append(tuple(center + (across * math.cos(theta) + along * math.sin(theta)) * r))
    faces = [tuple(range(sides - 1, -1, -1))]
    for i in range(len(points) - 1):
        for j in range(sides):
            faces.append((i*sides+j, i*sides+(j+1)%sides, (i+1)*sides+(j+1)%sides, (i+1)*sides+j))
    faces.append(tuple((len(points)-1)*sides+j for j in range(sides)))
    return smooth(mesh(name, verts, faces, collection, parent, mat))


def empty(name, location, collection, parent):
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    return obj


def animate(obj, frames, action_name):
    for frame, location, rotation in frames:
        obj.location = location
        obj.rotation_euler = rotation
        obj.keyframe_insert(data_path='location', frame=frame)
        obj.keyframe_insert(data_path='rotation_euler', frame=frame)
    obj.animation_data.action.name = action_name
    obj['loop_seconds'] = 4


def crystal(name, height, width, location, rotation, collection, parent, mats):
    sides = 6
    verts = [(0, 0, 0)]
    for z, rad in [(height*.23, width*.88), (height*.69, width), (height*.84, width*.72)]:
        for i in range(sides):
            a = i*math.tau/sides
            verts.append((rad*math.cos(a), rad*math.sin(a), z))
    verts.append((width*.12, -width*.08, height))
    faces = []
    for i in range(sides):
        j = (i+1)%sides
        faces.append((0, 1+j, 1+i))
        faces.append((1+i, 1+j, 7+j, 7+i))
        faces.append((7+i, 7+j, 13+j, 13+i))
        faces.append((13+i, 13+j, 19))
    obj = mesh(name, verts, faces, collection, parent, None)
    for mat in mats:
        obj.data.materials.append(mat)
    for i, polygon in enumerate(obj.data.polygons):
        polygon.material_index = i % len(mats)
    obj.location = location
    obj.rotation_euler = rotation
    return obj


def star(name, location, size, collection, parent, mat):
    verts = [(0, 0, size), (size*.55, 0, 0), (0, 0, -size), (-size*.55, 0, 0), (0, size*.24, 0), (0, -size*.24, 0)]
    return mesh(name, verts, [(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)], collection, parent, mat)


# 1. Moon Crystal: faceted crystals levitate above a moss-and-brass reliquary.
collection, root = asset('Moon Crystal')
cylinder('Moon • slate foot', (0,0,.07), .58,.14,collection,root,stone)
cylinder('Moon • brass inset', (0,0,.145), .54,.04,collection,root,gold)
cylinder('Moon • velvet moss bed',(0,0,.205),.50,.09,collection,root,moss)
ring('Moon • engraved brass rim',(0,0,.25),.50,.018,collection,root,gold_light)
for i in range(10):
    a=i*math.tau/10
    sphere('Moon • moss cushion %02d'%i,(math.cos(a)*.38,math.sin(a)*.38,.27),(.15,.13,.07),collection,root,moss_light)
float_root=empty('Moon • floating crystal assembly',(0,0,.27),collection,root)
crystal('Moon • great six-sided prism',1.52,.235,(0,.01,.14),(0,-.08,.2),collection,float_root,[cyan,cyan_dark,moon_white,lilac])
for i in range(5):
    a=i*math.tau/5+.25
    crystal('Moon • satellite prism %02d'%i,.66+i*.07,.12,(math.cos(a)*.27,math.sin(a)*.27,.025),(math.sin(a)*.30,-math.cos(a)*.30,a),collection,float_root,[cyan,moon_white,lilac])
ring('Moon • floating brass orbit',(0,0,.83),.42,.012,collection,float_root,gold_light,(.28,.18,0))
sphere('Moon • living heartlight',(.39,-.10,.95),(.067,.067,.067),collection,float_root,glow)
for i,(x,y,z) in enumerate([(-.34,-.08,1.46),(.41,.12,1.25),(-.20,.18,.73)]):
    sparkle=star('Moon • sparkle %02d'%i,(0,0,0),.10,collection,float_root,moon_white)
    sparkle.location=(x,y,z)
animate(float_root,[(1,(0,0,.27),(0,0,-.08)),(25,(0,0,.315),(0,0,0)),(49,(0,0,.34),(0,0,.08)),(73,(0,0,.30),(0,0,0)),(97,(0,0,.27),(0,0,-.08))],'Moon Crystal • floating light • four seconds')

# 2. Elder Tree: a curved, rooted elder with layered leaves and small lanterns.
collection, root = asset('Elder Tree')
cylinder('Elder • slate island',(0,0,.065),.64,.13,collection,root,stone)
cylinder('Elder • moss island',(0,0,.145),.61,.09,collection,root,moss)
for i in range(7):
    a=i*math.tau/7
    tube('Elder • spreading root %02d'%i,[(0,0,.35,.13),(math.cos(a)*.26,math.sin(a)*.26,.22,.095),(math.cos(a)*.55,math.sin(a)*.55,.18,.035)],.1,collection,root,wood,8)
tube('Elder • curved trunk',[(0,0,.18,.22),(-.08,.02,.50,.19),(.04,.01,.83,.17),(.00,.05,1.14,.135),(-.12,.04,1.48,.09),(-.10,.02,1.69,.025)],.15,collection,root,wood,10)
branches=[[(0,0,.9,.10),(-.32,.02,1.18,.075),(-.54,.03,1.48,.035)],[(0,.02,1.02,.10),(.31,.02,1.24,.075),(.52,.07,1.51,.025)],[(.0,.02,.72,.08),(.10,.29,1.1,.06),(.05,.42,1.46,.025)]]
for i,points in enumerate(branches):
    tube('Elder • story branch %02d'%i,points,.08,collection,root,wood_light)
for i in range(4):
    x=-.12+i*.07
    tube('Elder • carved bark line %02d'%i,[(x,-.155,.38,.006),(x+.025,-.17,.65,.006),(x-.01,-.14,.87,.004)],.006,collection,root,wood_dark,5)
for x in [-.075,.075]:
    sphere('Elder • kind golden eye',(x,-.166,.91),(.024,.018,.035),collection,root,gold_light)
tube('Elder • little smile',[(-.055,-.172,.80,.008),(0,-.185,.78,.008),(.055,-.172,.80,.008)],.008,collection,root,gold_light,5)
canopy=empty('Elder • swaying leaf crown',(0,0,1.15),collection,root)
clusters=[(-.45,.00,.38,.35,.30,.31),(-.15,.07,.60,.37,.32,.35),(.20,.02,.54,.37,.31,.35),(.48,.07,.31,.30,.26,.28),(.05,.31,.36,.36,.32,.30),(-.20,-.17,.33,.34,.28,.28),(.21,-.18,.28,.34,.27,.27),(-.04,.04,.81,.27,.25,.26)]
for i,(x,y,z,sx,sy,sz) in enumerate(clusters):
    sphere('Elder • layered crown %02d'%i,(x,y,z),(sx,sy,sz),collection,canopy,[leaf_a,leaf_b,leaf_c][i%3],2)
for i in range(19):
    a=i*2.399963
    x=math.cos(a)*(.27+(i%3)*.12);y=math.sin(a)*(.19+(i%3)*.08);z=.35+(i%4)*.09
    leaf=mesh('Elder • pointed leaf %02d'%i,[(-.14,0,0),(0,-.055,.02),(.17,0,0),(0,.055,.02),(0,0,.065)],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,3,2,1)],collection,canopy,[leaf_b,leaf_c][i%2])
    leaf.location=(x,y-.11,z)
    leaf.rotation_euler=(.2,math.sin(a)*.3,a)
for i,(x,y,z) in enumerate([(-.43,-.12,.18),(.37,-.07,.22),(.07,-.25,.40)]):
    tube('Elder • lantern thread %02d'%i,[(x,y,z+.18,.006),(x,y,z,.006)],.006,collection,canopy,gold,5)
    ring('Elder • lantern brass halo %02d'%i,(x,y,z),.065,.008,collection,canopy,gold_light,(math.pi/2,0,0))
    sphere('Elder • hanging lilac light %02d'%i,(x,y,z),(.043,.043,.059),collection,canopy,lilac_glow)
animate(canopy,[(1,(0,0,1.15),(0,-.025,-.014)),(25,(0,0,1.15),(.018,0,.007)),(49,(0,0,1.15),(0,.025,.014)),(73,(0,0,1.15),(-.018,0,-.007)),(97,(0,0,1.15),(0,-.025,-.014))],'Elder Tree • leaves in the breeze • four seconds')

# 3. Treasure Chest: separate oak boards, curved lid, brass bindings, cyan velvet.
collection, root = asset('Treasure Chest')
for x in [-.54,.54]:
    for y in [-.30,.30]:
        cube('Chest • brass claw foot',(x,y,.105),(.19,.19,.21),collection,root,gold,.045)
cube('Chest • bottom oak floor',(0,0,.235),(1.37,.86,.16),collection,root,chest_wood,.04)
cube('Chest • velvet interior floor',(0,0,.33),(1.23,.71,.055),collection,root,inside,.02)
for i in range(6):
    x=-.575+i*.23
    for y in [-.415,.415]:
        cube('Chest • hand-cut wall board %02d'%i,(x,y,.56),(.225,.10,.53),collection,root,[chest_wood,chest_alt][i%2],.025)
for x in [-.665,.665]:
    cube('Chest • shaped end wall',(x,0,.56),(.11,.78,.53),collection,root,chest_wood,.025)
for x in [-.48,.48]:
    for y in [-.48,.48]:
        cube('Chest • vertical brass binding',(x,y,.55),(.078,.035,.59),collection,root,gold,.012)
    cube('Chest • lower brass wrap',(x,0,.255),(.078,.94,.045),collection,root,gold,.012)
for x in [-.55,-.38,.38,.55]:
    sphere('Chest • front brass rivet',(x,-.505,.41),(.022,.013,.022),collection,root,gold_light)
for y in [-.46,.46]:
    cube('Chest • upper brass lip',(0,y,.83),(1.44,.045,.045),collection,root,gold_light,.012)
cube('Chest • glowing heartlight inside',(0,0,.40),(1.10,.58,.04),collection,root,glow,.02)
for i in range(3):
    crystal('Chest • tucked moon gem %02d'%i,.24,.085,(-.29+i*.29,.04,.41),(0,(i-1)*.27,i*.6),collection,root,[cyan,lilac,moon_white])
hinge=empty('Chest • breathing curved lid',(0,.43,.84),collection,root)


def lid_strip(name, xmin, xmax, mat):
    count=12;verts=[]
    for x in [xmin,xmax]:
        for radius, height_offset in [(.445,0),(.402,-.025)]:
            for i in range(count+1):
                a=i*math.pi/count
                verts.append((x,radius*math.cos(a)-.43,.37*math.sin(a)+height_offset))
    stride=(count+1)*2;faces=[]
    for i in range(count):
        faces.extend([(i,i+1,stride+i+1,stride+i),(count+1+i,stride+count+1+i,stride+count+2+i,count+2+i),
                      (i,count+1+i,count+2+i,i+1),(stride+i,stride+i+1,stride+count+2+i,stride+count+1+i)])
    faces.extend([(0,stride,stride+count+1,count+1),(count,count+count+1,stride+count+count+1,stride+count)])
    return mesh(name,verts,faces,collection,hinge,mat)


for i in range(6):
    lid_strip('Chest • curved oak lid plank %02d'%i,-.71+i*.238,-.71+(i+1)*.238-.008,[chest_wood,chest_alt][i%2])
for x in [-.49,.49]:
    lid_strip('Chest • arched brass lid strap',x-.037,x+.037,gold)
for x in [-.735,.735]:
    lid_strip('Chest • lid edge binding',x-.012,x+.012,gold_light)
cube('Chest • front key plate',(0,-.495,.62),(.19,.035,.23),collection,root,gold_light,.04)
sphere('Chest • cyan lock jewel',(0,-.523,.65),(.041,.016,.05),collection,root,cyan)
cube('Chest • keyhole stem',(0,-.531,.585),(.025,.008,.05),collection,root,inside,.005)
cube('Chest • lid latch',(0,-.90,.028),(.115,.035,.16),collection,hinge,gold_light,.025)
for x in [-.45,.45]:
    cylinder('Chest • rear hinge pin',(x,.43,.84),.043,.14,collection,root,gold,12).rotation_euler=(0,math.pi/2,0)
animate(hinge,[(1,(0,.43,.84),(-.18,0,0)),(25,(0,.43,.84),(-.40,0,0)),(49,(0,.43,.84),(-.66,0,0)),(73,(0,.43,.84),(-.40,0,0)),(97,(0,.43,.84),(-.18,0,0))],'Treasure Chest • a secret waking • four seconds')

# Export each self-contained collection while its root is centered at the origin.
scene.frame_set(1)
files=['moon-crystal.glb','elder-tree.glb','treasure-chest.glb']
report=[]
for (name,collection,root),filename in zip(assets,files):
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in collection.all_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=root
    export_options = dict(filepath=OUTPUT+filename, export_format='GLB', use_selection=True, export_animations=True, export_yup=True, export_frame_range=True)
    export_properties = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
    if 'export_active_scene' in export_properties:
        export_options['export_active_scene'] = True
    bpy.ops.export_scene.gltf(**export_options)
    faces=sum(len(obj.data.polygons) for obj in collection.all_objects if obj.type=='MESH')
    report.append(dict(asset=name,file=filename,objects=len(collection.all_objects),base_faces=faces,loop_seconds=4))

# Arrange a separate hero composition in the saved editable source.
for (_,_,root),x in zip(assets,[-2.2,0,2.2]):
    root.location=(x,0,0)
studio=bpy.data.collections.new('Heartlight • Hero Studio (not exported)')
scene.collection.children.link(studio)
cube('Studio • midnight floor',(0,0,-.105),(200,200,.10),studio,None,material('Studio midnight',(0.018,.036,.062),roughness=.65),0)
for name,location,power,size,color in [
 ('Key softbox',(-3,-4,6),1100,5,(.72,.87,1)),
 ('Warm rim',(3,2,5),1300,4,(1,.70,.35)),
 ('Cyan fill',(0,-1,4),700,3,(.35,1,.94))]:
    light_data=bpy.data.lights.new('Heartlight • '+name,'AREA')
    light_data.energy=power;light_data.shape='DISK';light_data.size=size;light_data.color=color
    light=bpy.data.objects.new('Heartlight • '+name,light_data);studio.objects.link(light);light.location=location
    light.rotation_euler=(Vector((0,0,.8))-light.location).to_track_quat('-Z','Y').to_euler()
camera_data=bpy.data.cameras.new('Heartlight • landmark hero camera')
camera=bpy.data.objects.new('Heartlight • landmark hero camera',camera_data)
studio.objects.link(camera);camera.location=(5,-10,5.0)
camera.rotation_euler=(Vector((0,0,.85))-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.type='ORTHO';camera_data.ortho_scale=8.5;scene.camera=camera
scene.frame_set(25)
scene.render.filepath=PREVIEW
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
bpy.ops.render.render(write_still=True)
print(json.dumps({'heartlight_assets':report,'blend':BLEND,'preview':PREVIEW,'scene':scene.name}))
