function [score] = AUC_Judd(map1, map2)
% map1: Saliency map
% map2: Fixation pts

jitter = 1; % Add tiny non-zero random constant to all map locations to ensure ROC can be calculated robustly (to avoid uniform region)
score = nan;

if jitter
    % jitter the saliency map slightly to distrupt ties of the same numbers
    map1 = map1+rand(size(map1))/10000000;
end
% normalize saliency map
map1 = (map1-min(map1(:)))/(max(map1(:))-min(map1(:)));

if sum(isnan(map1(:)))==length(map1(:))
    disp('NaN saliencyMap');
    return
end

S = map1(:);
F = map2(:);
Sth = S(F>0); % sal map values at fixation locations
Nfixations = length(Sth);
Npixels = length(S);

allthreshes = sort(Sth, 'descend'); % sort sal map values, to sweep through values
tp = zeros(Nfixations+2,1);
fp = zeros(Nfixations+2,1);
tp(1)=0; tp(end) = 1; 
fp(1)=0; fp(end) = 1;

for i = 1:Nfixations
    thresh = allthreshes(i);
    aboveth = sum(S >= thresh); % total number of sal map values above threshold
    tp(i+1) = i / Nfixations; % ratio sal map values at fixation locations above threshold
    fp(i+1) = (aboveth-i) / (Npixels - Nfixations); % ratio other sal map values above threshold
end 

score = trapz(fp,tp);
allthreshes = [1;allthreshes;0];

% toPlot = 0;
% if toPlot
%     subplot(121); imshow(map1, []); title('SaliencyMap with fixations to be predicted');
%     hold on;
%     [y, x] = find(map2);
%     plot(x, y, '.r');
%     subplot(122); plot(fp, tp, '.b-');   title(['Area under ROC curve: ', num2str(score)])
% end

end

