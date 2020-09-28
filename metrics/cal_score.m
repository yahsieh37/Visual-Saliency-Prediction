clear;

% Path to inputs
model_name = 'MSI-SAv6';  % For saving scores
FixMapdir = './FixationMap';
FixPtsdir = './FixationPts';
SalMapdir = '../MSI_exp/results_SAv6';
FixMap = dir(FixMapdir);
FixPts = dir(FixPtsdir);
SalMap = dir(SalMapdir);

% Initialize scores
KL_score = zeros(1,length(FixMap)-2);
NSS_score = zeros(1,length(FixMap)-2);
SIM_score = zeros(1,length(FixMap)-2);
EMD_score = zeros(1,length(FixMap)-2);
CC_score = zeros(1,length(FixMap)-2);
AUC_Judd_score = zeros(1,length(FixMap)-2);
AUC_Borji_score = zeros(1,length(FixMap)-2);
AUC_shuff_score = zeros(1,length(FixMap)-2);

% Calculate scores
for k=3:length(FixMap)
%for k=3:6
    fprintf('Image count = %d \n', k-2);
    fmap = imread(fullfile(FixMapdir,FixMap(k).name));
    fpts = imread(fullfile(FixPtsdir,FixPts(k).name));
    smap = imread(fullfile(SalMapdir,SalMap(k).name));

    fmap = im2double(fmap);
    fpts = im2double(fpts);
    smap = im2double(imresize(smap, size(fmap)));
    % Random sample 10 maps for sAUC
    samp_map = rnd_sample(fpts, 10, k);

    % Calculate scores
    KL_score(k-2) = KL(smap, fmap);
    NSS_score(k-2) = NSS(smap, fpts);
    SIM_score(k-2) = SIM(smap, fmap);
    %EMD_score(k-2) = EMD(smap, fmap);  % Slow
    CC_score(k-2) = CC(smap, fmap);
    AUC_Judd_score(k-2) = AUC_Judd(smap, fpts);
    AUC_Borji_score(k-2) = AUC_Borji(smap, fpts);
    AUC_shuff_score(k-2) = AUC_shuffled(smap, fpts, samp_map);

end

% % % Save scores
save(fullfile('scores',strcat(model_name,'_KL.mat')), 'KL_score');
save(fullfile('scores',strcat(model_name,'_NSS.mat')), 'NSS_score');
save(fullfile('scores',strcat(model_name,'_SIM.mat')), 'SIM_score');
% save(fullfile('scores',strcat(model_name,'_EMD.mat')), 'EMD_score');
save(fullfile('scores',strcat(model_name,'_CC.mat')), 'CC_score');
save(fullfile('scores',strcat(model_name,'_AUC_Judd.mat')), 'AUC_Judd_score');
save(fullfile('scores',strcat(model_name,'_AUC_Borji.mat')), 'AUC_Borji_score');
save(fullfile('scores',strcat(model_name,'_AUC_shuff.mat')), 'AUC_shuff_score');
 
% Print mean scores
fprintf('KL = %.4f \nNSS = %.4f \n', mean(KL_score), mean(NSS_score));
fprintf('SIM = %.4f \n', mean(SIM_score));
% fprintf('EMD = %.4f \n', mean(EMD_score));
fprintf('CC = %.4f \n', mean(CC_score));
fprintf('AUC_Judd = %.4f \n', mean(AUC_Judd_score));
fprintf('AUC_Borji = %.4f \n', mean(AUC_Borji_score));
fprintf('AUC_shuff = %.4f \n', mean(AUC_shuff_score));