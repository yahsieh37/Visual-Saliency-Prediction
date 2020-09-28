function [out_map] = rnd_sample(ori_map,n_sample, img_idx)
% Random sample n_sample images and union the fixation points for calculating sAUC

FixPtsdir = './FixationPts';
FixPts = dir(FixPtsdir);

% Get the sampling index (not include the original image)
r = [img_idx];
while find(r == img_idx)
    r = randi([3 1003],1,n_sample);
end

% Generate union of fixation points
img_s = size(ori_map);
out_map = zeros(img_s);

for i = 1:n_sample
    fpts = imread(fullfile(FixPtsdir,FixPts(r(i)).name));
    fpts = im2double(imresize(fpts, img_s));
    fpts(fpts<0.5) = 0;
    out_map = fpts | out_map;
end
out_map = double(out_map);

end

