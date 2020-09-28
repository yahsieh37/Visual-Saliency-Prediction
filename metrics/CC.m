function [score] = CC(map1, map2)
% map1: Saliency map
% map2: Fixation map

% normalize both maps
map1 = (map1 - mean(map1(:))) / std(map1(:)); 
map2 = (map2 - mean(map2(:))) / std(map2(:)); 

score = corr2(map2, map1);

end

