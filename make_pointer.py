#!/usr/bin/env python3
#%%
# Set parameters and import needed modules
import pyvista as pv
import numpy as np

# all dimensions in mm
# mating pen dimensions
pen_l = 35.0
pen_dmin = 10.0
pen_dmax = 11.0

# fabrication/design
wrist_taper = 15
wall_t = 2.0
z_clearance= 3
r_clearance = 0.5
nseg = 100

# %%
# Adjust alignment to center on origin

orig_stl = pv.read('pointer_isolated.stl')

#redefine coordinate system so "wrist" is at origin
orig_bb = np.array(orig_stl.bounds)
xform =0.5*(orig_bb[::2] + orig_bb[1::2])
xform[2] = orig_bb[4] # set z to bottom of pointer
xform += np.array([.65,-1.15,0]) # shift to center of pointer, determined by eye
aligned_orig = orig_stl.translate(-xform)

p = pv.Plotter()
p.add_mesh(aligned_orig, color='orange')
p.add_mesh(pv.Circle(radius=3), color='blue', opacity=0.5)
p.enable_parallel_projection()
p.show_bounds(n_xlabels=20,n_ylabels=20)
p.show_axes_all()
p.show_grid()
p.show()
pv.Circle()
# %%
# Modify tip of pointer (z=25 to 40mm) for added pointiness

# span of finger taper
zmax = 40
zmin = 25

# max squeeze at tip of taper
squeeze_mm = 2

# Get the tip of the pointer
orig_pts = aligned_orig.points.copy()
aligned_orig.compute_normals(inplace=True)

new_pts = orig_pts.copy()
is_tip = (new_pts[:,2] > zmin) & (new_pts[:,2] < zmax)
zfactor = np.zeros((sum(is_tip),3))
zfactor[:,1] = (new_pts[is_tip,2]-zmin)/(zmax-zmin)

new_pts[is_tip] -= aligned_orig.point_normals[is_tip]*zfactor*squeeze_mm

# fix indentation
is_driver = new_pts[:,2]<9
in_radius = new_pts[:,0]**2 + new_pts[:,1]**2 < 2.5**2
is_driver = is_driver & in_radius
new_pts[is_driver,2] =0

# Create new mesh
new_stl = pv.PolyData(new_pts, aligned_orig.faces)
p = pv.Plotter()
p.add_mesh(new_stl, color='blue')
p.add_mesh(aligned_orig, color='orange', opacity=0.5)
p.enable_parallel_projection()
p.show()

# %%
# build the pen adapter

def make_pen_adapter(wall=0):
    zcyl = wall+pen_l
    cyl = pv.Cylinder(radius=wall+pen_dmax/2, height=zcyl, direction=(0,0,1),capping=True).triangulate()
    is_top = cyl.points[:,2] == zcyl/2
    cyl.translate([0,0,-zcyl/2], inplace=True)

    k_taper = (2*wall+pen_dmin)/(2*wall+pen_dmax)
    
    cyl.points[is_top] *= k_taper

    if wall == 0:
        #inner taper of 45 degrees
        cone_z = pen_dmin/2
        cone_r = cone_z
    else:
        cone_r = wall+pen_dmin/2
        cone_z = cone_r/np.tan(wrist_taper*np.pi/180)
    cone = pv.Cone(radius=cone_r, height=cone_z, direction=(0,0,1),resolution=nseg).triangulate()
    # cone.plot(style='wireframe')
    cone.translate([0,0,cone_z/2-0.1], inplace=True)

    pen = cyl.boolean_union(cone)

    return pen

zshift = -3.5/np.tan(wrist_taper*np.pi/180)

wall = make_pen_adapter(wall_t).translate((0,0,zshift))
pen = make_pen_adapter().translate((0,0,zshift-2.5))

# plot the pen
p = pv.Plotter()
p.add_mesh(pen, color='red')
p.add_mesh(wall, color='green',opacity=0.5)
# p.add_mesh(cone, color='red')
p.add_mesh(new_stl, color='blue', opacity=0.5)
p.enable_parallel_projection()
p.show()

# %%
# perform final boolean operations

body = new_stl.boolean_union(wall)
result = body.boolean_difference(pen)
result.plot(style='wireframe')

result.save('python-generated.stl')