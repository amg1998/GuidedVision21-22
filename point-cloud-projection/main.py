#!/usr/bin/env python3
import json
import os
import tempfile
import platform
from pathlib import Path
import ransac
import open3d as o3d


import cv2
import depthai
import numpy


try:
    from projector_3d import PointCloudVisualizer
except ImportError as e:
    raise ImportError(f"\033[1;5;31mError occured when importing PCL projector: {e} \033[0m ")


device = depthai.Device("", False)
pipeline = device.create_pipeline(config={
    'streams': ['right', 'depth'],
    'ai': {
        "blob_file": str(Path('./mobilenet-ssd/mobilenet-ssd.blob').resolve().absolute()),
    },
    'camera': {'mono': {'resolution_h': 720, 'fps': 30}},
})

if pipeline is None:
    raise RuntimeError("Error creating a pipeline!")

right = None
pcl_converter = None
vis = o3d.visualization.Visualizer()
vis.create_window()
isstarted = False
while True:
    data_packets = pipeline.get_available_data_packets()
    # pcd_x = o3d.geometry.PointCloud()
    # pcd_y = o3d.geometry.PointCloud()
    # pcd_z = o3d.geometry.PointCloud()

    #make box with dots
    # pcd_pfront = o3d.geometry.PointCloud()
    # pcd_pback = o3d.geometry.PointCloud()
    # pcd_pmid = o3d.geometry.PointCloud()

    # #red points
    # x_arr = numpy.asarray([[0,0,0],[2,0,0]]) 
    # # blue points
    # y_arr = numpy.asarray([[0,0,0],[0,2,0]]) 
    # # green points
    # z_arr = numpy.asarray([[0,0,0],[0,0,2]]) 
    # pcd_x.points = o3d.utility.Vector3dVector(x_arr)
    # pcd_y.points = o3d.utility.Vector3dVector(y_arr)
    # pcd_z.points = o3d.utility.Vector3dVector(z_arr)
    # pcd_x.paint_uniform_color([1,0,0])
    # pcd_y.paint_uniform_color([0,1,0])
    # pcd_z.paint_uniform_color([0,0,1])

    #to get prism
    corners = numpy.asarray([[0,0,0.7],[1,0,0.7],[1,2.14,0.7],[0,2.14,0.7],[0,0,2],[1,0,2],[1,2.14,2],[0,2.14,2]])
    bounds = corners.astype("float64")
    bounds = o3d.utility.Vector3dVector(bounds)
    oriented_bounding_box = o3d.geometry.OrientedBoundingBox.create_from_points(bounds)
    
    
    #to make box with dots
    # cube_pfront = numpy.asarray([[0,0,0.7],[1,0,0.7],[1,2.14,0.7],[0,2.14,0.7],[0,1.07,0.7],[1,1.07,0.7],[0.5,0,0.7],[0.5,2.14,0.7]])
    # cube_pback = numpy.asarray([[0,0,2],[1,0,2],[1,2.14,2],[0,2.14,2],[0,1.07,2],[1,1.07,2],[0.5,0,2],[0.5,2.14,2]])
    # cube_pmid = numpy.asarray([[0,0,1.35],[1,0,1.35],[0,2.14,1.35],[1,2.14,1.35],[0,1.07,1.35],[1,1.07,1.35],[0.5,0,1.35],[0.5,2.14,1.35]])
    # pcd_pmid.points = o3d.utility.Vector3dVector(cube_pmid)
    # pcd_pfront.points = o3d.utility.Vector3dVector(cube_pfront)
    # pcd_pback.points = o3d.utility.Vector3dVector(cube_pback)
    # pcd_pfront.paint_uniform_color([1,0,0])
    # pcd_pback.paint_uniform_color([0,1,0])
    # pcd_pmid.paint_uniform_color([0,0,1])

    for packet in data_packets:
        if packet.stream_name == "right":
            right = packet.getData()
            #cv2.imshow(packet.stream_name, right)
        elif packet.stream_name == "depth":
            frame = packet.getData()
            median = cv2.medianBlur(frame, 5)
            median2 = cv2.medianBlur(median,5)
            '''
            median3 = cv2.medianBlur(median,5)
            median4 = cv2.medianBlur(median,5)
            median5 = cv2.medianBlur(median,5)

            bilateral = cv2.bilateralFilter(frame,15,75,75)
            '''
            if right is not None:

                if pcl_converter is None:
                    fd, path = tempfile.mkstemp(suffix='.json')
                    with os.fdopen(fd, 'w') as tmp:
                        json.dump({
                            "width": 1280,
                            "height": 720,
                            "intrinsic_matrix": [item for row in device.get_right_intrinsic() for item in row]
                        }, tmp)

                    pcl_converter = PointCloudVisualizer(path)
                pcd = pcl_converter.rgbd_to_projection(median, right)

                #to get points within bounding box
                num_pts = oriented_bounding_box.get_point_indices_within_bounding_box(pcd.points)
                # cropped_pcd = pcd.crop(oriented_bounding_box)

                if not isstarted:
                    vis.add_geometry(pcd)
                    # vis.add_geometry(pcd_x)
                    # vis.add_geometry(pcd_y)
                    # vis.add_geometry(pcd_z)
                    vis.add_geometry(oriented_bounding_box)
                    # vis.add_geometry(pcd_pback)
                    # vis.add_geometry(pcd_pfront)
                    # vis.add_geometry(pcd_pmid)
                    isstarted = True       
                             	
                else:
                    vis.update_geometry(pcd)
                    # vis.update_geometry(pcd_x)
                    # vis.update_geometry(pcd_y)
                    # vis.update_geometry(pcd_z)
                    # vis.update_geometry(pcd_pback)
                    # vis.update_geometry(pcd_pmid)
                    # vis.update_geometry(pcd_pfront)
                    vis.update_geometry(oriented_bounding_box)
                    vis.poll_events()
                    vis.update_renderer()

                print("num_pts: ", len(num_pts))
                # print("X", numpy.shape(numpy.asarray(pcd.points)[:,0]))
                # print("Y", numpy.shape(numpy.asarray(pcd.points)[:,1]))
                # print("Z", numpy.shape(numpy.asarray(pcd.points)[:,2]))

                # print(numpy.asarray((pcd.points)))
                # print(numpy.shape(numpy.asarray((pcl_converter.pcl.points))))
                # pointsc = numpy.asarray((pcl_converter.pcl.points))
                # pointspcd = numpy.asarray((pcd.points))
                # print("X max: , X min: ",max(pointsc[:,0]),min(pointsc[:,0]), max(pointspcd[:,0]),min(pointspcd[:,0]))
                # print("Y max: , Y min: ",max(pointsc[:,1]),min(pointsc[:,1]), max(pointspcd[:,1]),min(pointspcd[:,1]))
                # print("Z max: , Z min: ",max(pointsc[:,2]),min(pointsc[:,2]), max(pointspcd[:,2]),min(pointspcd[:,2]))


                # x,y,z = ransac.find_plane(pcd)
                # ransac.show_graph(x,y,z)
            # cv2.imshow(packet.stream_name, frame)
            '''
            cv2.imshow("filter", median)
			'''
            # cv2.imshow("filter2", median2)
            '''
            cv2.imshow("filter3", median3)
            cv2.imshow("filter4", median4)
            '''
            #cv2.imshow("filter5", median5)


            #cv2.imshow("filter2", bilateral)

    if cv2.waitKey(1) == ord("q"):
        break

if pcl_converter is not None:
    pcl_converter.close_window()