function [score] = AUC_Borji(map1, map2)
% map1: Saliency map
% map2: Fixation pts

stepSize = .1; % for sweeping through saliency map
Nsplits = 100; % number of random splits
score=nan;

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

% for each fixation, sample Nsplits values from anywhere on the sal map
r = randi([1 Npixels],[Nfixations,Nsplits]);
randfix = S(r); % sal map values at random locations

% calculate AUC per random split (set of random locations)
auc = nan(1,Nsplits);
for s = 1:Nsplits
    
    curfix = randfix(:,s);
    
    allthreshes = fliplr([0:stepSize:double(max([Sth;curfix]))]);
    tp = zeros(length(allthreshes)+2,1);
    fp = zeros(length(allthreshes)+2,1);
    tp(1)=0; tp(end) = 1; 
    fp(1)=0; fp(end) = 1; 
    
    for i = 1:length(allthreshes)
        thresh = allthreshes(i);
        tp(i+1) = sum((Sth >= thresh))/Nfixations;
        fp(i+1) = sum((curfix >= thresh))/Nfixations;
    end

    auc(s) = trapz(fp,tp);
end

score = mean(auc); % mean across random splits

% toPlot = 1;
% if toPlot
%     subplot(121); imshow(map1, []); title('SaliencyMap with fixations to be predicted');
%     hold on;
%     [y, x] = find(map2);
%     plot(x, y, '.r');
%     subplot(122); plot(fp, tp, '.b-');   title(['Area under ROC curve: ', num2str(score)])
% end

end

