from sectionproperties.pre.library import circular_hollow_section, elliptical_hollow_section, rectangular_hollow_section, polygon_hollow_section, i_section, mono_i_section, tapered_flange_i_section, channel_section, tapered_flange_channel, tee_section, angle_section, cee_section, zed_section, box_girder_section, bulb_section
from sectionproperties.analysis import Section

def main():


    geom = i_section(d=300, b=300, t_f=19, t_w=11, r=27, n_r=10)         # HEB 300
    geom.create_mesh(mesh_sizes=10)
    sec = Section(geometry=geom)
    sec.plot_mesh(materials=False, pause = False)
    sec.calculate_geometric_properties()
    sec.calculate_warping_properties()
    sec.calculate_stress(n=50e3, m11=5e6)


if __name__ == "__main__":
    main()
