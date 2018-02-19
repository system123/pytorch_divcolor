import os
os.environ["CUDA_VISIBLE_DEVICES"]="0"
import sys


import numpy as np
import caffe
import skimage.color as color
import skimage.io
import scipy.ndimage.interpolation as sni
import glob
from tqdm import tqdm

def save_zhang_feats(img_fns, ext='png', dest='gray_fts'):

	gpu_id = 0
	caffe.set_mode_gpu()
	caffe.set_device(gpu_id)
	net = caffe.Net('colorization_zhang/colorization/models/colorization_deploy_v1.prototxt', \
    'colorization_zhang/colorization/models/colorization_release_v1.caffemodel', caffe.TEST)

	(H_in,W_in) = net.blobs['data_l'].data.shape[2:] # get input shape
	(H_out,W_out) = net.blobs['class8_ab'].data.shape[2:] # get output shape
	net.blobs['Trecip'].data[...] = 6/np.log(10) # 1/T, set annealing temperature

	feats_fns = []
	for img_fn_i, img_fn in enumerate(tqdm(img_fns)):

		npz_fn = img_fn.replace(ext, 'npz')
		npz_fn = os.path.join( dest, os.path.basename(npz_fn) )

		if not os.path.isfile(npz_fn):
			# load the original image
			img_rgb = caffe.io.load_image(img_fn)
			img_lab = color.rgb2lab(img_rgb) # convert image to lab color space
			img_l = img_rgb[:,:,0] # pull out L channel
			(H_orig,W_orig) = img_rgb.shape[:2] # original image size

			# create grayscale version of image (just for displaying)
			img_lab_bw = img_lab.copy()
			img_lab_bw[:,:,1:] = 0
			img_rgb_bw = color.lab2rgb(img_lab_bw)

			# resize image to network input size
			img_rs = caffe.io.resize_image(img_rgb,(H_in,W_in)) # resize image to network input size
			img_lab_rs = color.rgb2lab(img_rs)
			img_l_rs = img_lab_rs[:,:,0]

			net.blobs['data_l'].data[0,0,:,:] = img_l_rs-50 # subtract 50 for mean-centering
			net.forward() # run network

			np.savez_compressed(npz_fn, net.blobs['conv7_3'].data)

		feats_fns.append(npz_fn)

	return feats_fns

if __name__=="__main__":
	img_fns = glob.glob('sar/*.png')
	feats_fns = save_zhang_feats(img_fns, ext='png')

	with open('gray_fts/list.txt', 'w') as fp:
		for feats_fn in feats_fns:
			fp.write('%s\n' % feats_fn)
