function [score] = NSS(map1,map2)
% map1: Saliency map
% map2: Fixation pts

% normalize saliency map
map1 = (map1 - mean(map1(:)))/std(map1(:)); 

% mean value at fixation locations
score = mean(map1(logical(map2)));

end

