from PIL import Image 
import numpy as np

# i. For each correspondence xi <-> xi' compute Ai
# ii. Assemble n 2x9 matrices Ai into a single 2nx9 matrix A
# iii. Obtain SVD of A. Solution for h is last column of V
# iv. Determine H from h
def homography(src_points, dest_points):
    A = []  # used to construct matrix needed for computing homography

    for i in range(src_points.shape[0]):  # looping through each point pair (x, y, z) given points
        x, y, z = src_points[i, :]
        xp, yp, zp = dest_points[i, :]
        A.append([0, 0, 0, -x, -y, -z, yp*x, yp*y, yp*z])
        A.append([x, y, z, 0, 0, 0, -xp*x, -xp*y, -xp*z])
    A = np.array(A)     

    # Computing SVD of A to obtain column V, the solution for h
    _, _, v = np.linalg.svd(A)  # SVD returns V^T, a row
    H = v[-1].reshape(3, 3)  # extracting v[-1], last row of v and reshaping into 3x3 matrix
    return H

def apply_transformation(src_img, dest_img, H): 
    dest_width, dest_height = dest_img # obtaining width and height of dest img to iterate through

    # Creating an empty image array for dest img
    # For each pixel defined by height and width, 3 values define its color (RGB)
    # Each value in array is an unsigned 8-bit int ranging from 0 to 255
    dest_empty_img = np.zeros((dest_height, dest_width, 3), dtype=np.uint8) 

    inverse_H = np.linalg.inv(H) # obtaining inverse of H for inverse warping

    # Iterating over each pixel in output image
    for i in range(dest_height):
        for j in range(dest_width):

            src_pos = np.dot(inverse_H, [j, i, 1]) # mapping pixel position from dest img back into src img
            src_x, src_y, _ = src_pos / src_pos[2] # normalizing to get cartesian coordinates

            # Perform 2d bilinear interpolation
            if 0 <= src_x < src_img.shape[1] and 0 <= src_y < src_img.shape[0]: # ensure position is within image bounds

                # Calculate the nearest pixel indices
                # .floor rounds a number to nearest int that is less than or equal to that number
                # .ceil performs the opposite, rounding to an int greater than or equal to that number
                # x_floor = j, y_floor = i, x_ceil = j+1, y_ceil = i+1
                x_floor, y_floor = np.floor([src_x, src_y]).astype(int)
                x_ceil, y_ceil = np.ceil([src_x, src_y]).astype(int)

                # Calculate weights a,b for interpolation
                a = src_x - x_floor # horizontal distance from exact position to left int position
                b = src_y - y_floor # vertical distance from position to bottom integer position
                
                # Compute the interpolated pixel value
                # Because images are stored in arrays, specifying row (corresponds to y coordinates) and vice versa
                bottom_left = src_img[y_floor, x_floor] # f[i, j]
                bottom_right = src_img[y_floor, x_ceil] # f[i, j+1]
                top_left = src_img[y_ceil, x_floor] # f[i+1, j]
                top_right = src_img[y_ceil, x_ceil] # f[i+1, j+1]

                interpolated_value = (1 - a)*(1 - b)*bottom_left + a*(1 - b)*bottom_right + (1 - a)*b*top_left + a*b*top_right
                dest_empty_img[i, j] = interpolated_value # replace interpolated value to dest image
    return Image.fromarray(dest_empty_img) # convert array to an image       

def find_intersection(line1, line2):
    l1 = np.array(line1)
    l2 = np.array(line2)
    intersection = np.cross(l1, l2) # calculate intersection point using cross product

    # Normalize if the last coordinate is not zero
    if intersection[-1] != 0:
        intersection = intersection / intersection[-1]
    return intersection

def main():
    src_img = Image.open('basketball-court.ppm')
    
    # DLT Algorithm for homography estimation using pixel feature locations
    src_points = np.array([[289, 313,1], [3, 198,1], [418, 69,1], [245, 44,1]])
    dest_points = np.array([[0, 0,1], [0, 499,1], [939, 0,1], [939, 499,1]])
    H_points = homography(src_points, dest_points)
    print("H from points:")
    print(H_points, "\n")
    warped_img1 = apply_transformation(np.array(src_img), (940, 500), H_points)
    warped_img1.save('dlt_using_points.jpg')
    warped_img1.show()

    # DLT Algorithm for homography estimation using line feature locations
    # src_lines and dest_lines were computed by taking the cross product of two points
    src_lines = np.array([[154,242,-48378],[-25,173,-1487],[-244,-129,110893],[115,-286,56283]])
    dest_lines = np.array([[0,939,-468561],[499,0,-468561],[0, -939, 0], [-499, 0,0]])
    src_intersected_points = np.array([find_intersection(src_lines[i], src_lines[(i + 1) % len(src_lines)]) for i in range(len(src_lines))])
    dest_intersected_points = np.array([find_intersection(dest_lines[i], dest_lines[(i + 1) % len(dest_lines)]) for i in range(len(dest_lines))])
    H_lines = homography(src_intersected_points, dest_intersected_points)
    print("H from lines:")
    print(H_lines, "\n")
    warped_img2 = apply_transformation(np.array(src_img), (940, 500), H_lines)
    warped_img2.save('dlt_using_lines.jpg')
    warped_img2.show()

main()



