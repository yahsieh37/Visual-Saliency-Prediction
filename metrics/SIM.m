function [score] = SIM(map1, map2)
% map1: Saliency map
% map2: Fixation map

if any(map1(:)) % zero map will remain a zero map
    map1= (map1-min(map1(:)))/(max(map1(:))-min(map1(:)));
    map1 = map1/sum(map1(:));
end
if any(map2(:)) % zero map will remain a zero map
    map2= (map2-min(map2(:)))/(max(map2(:))-min(map2(:)));
    map2 = map2/sum(map2(:));
end

score = nan;
if sum(isnan(map1(:)))==length(map1(:)) || sum(isnan(map2(:)))==length(map2(:))
    return;
end

% compute histogram intersection
diff = min(map1, map2);
score = sum(diff(:));

% toPlot = 0;
% % visual output
% if toPlot
%     subplot(131); imshow(map1, []);
%     subplot(132); imshow(map2, []);
%     subplot(133); imshow(diff, []);
%     %title(['Similar parts = ', num2str(s)]);
%     pause;
% end

end

