function [score] = KL(map1,map2)
% map1: Saliency map
% map2: Fixation map

%make sure map1 and map2 sum to 1
if any(map1(:))
    map1 = map1/sum(map1(:));
end
if any(map2(:))
    map2 = map2/sum(map2(:));
end

% compute KL-divergence
score = sum(sum(map2 .* log(eps + map2./(map1+eps))));

end

