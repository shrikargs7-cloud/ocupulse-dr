function lesions = lesion_detection(img, vessel_mask)
% LESION_DETECTION Detects microaneurysms, hemorrhages, exudates, and neovascularization
%
% Inputs:
%   img - RGB retinal fundus photograph
%   vessel_mask - Binary vessel mask (excluded to prevent false positives)
%
% Outputs:
%   lesions - Structure containing lesion counts, area, and bounding masks

if size(img, 3) == 3
    green = double(img(:, :, 2));
    red = double(img(:, :, 1));
else
    green = double(img);
    red = green;
end

roi_mask = green > 20;
non_vessel_roi = roi_mask & (~vessel_mask);

% 1. Optic Disc Mask (Brightest circular region - excluded from exudates)
disc_kernel = fspecial('disk', 15);
disc_candidate = imfilter(red, disc_kernel);
[~, max_idx] = max(disc_candidate(:));
[disc_r, disc_c] = ind2sub(size(red), max_idx);
[X, Y] = meshgrid(1:size(red, 2), 1:size(red, 1));
disc_mask = ((X - disc_c).^2 + (Y - disc_r).^2) <= (35^2);

% Non-disc, non-vessel search zone
search_zone = non_vessel_roi & (~disc_mask);

% 2. Microaneurysm Detection (Small dark circular spots: 2 to 12 px)
se_small = strel('disk', 4);
blackhat = imbothat(uint8(green), se_small);
ma_candidates = (double(blackhat) > 25) & search_zone;
ma_cc = bwconncomp(ma_candidates);
ma_props = regionprops(ma_cc, 'Area', 'Eccentricity');
ma_count = 0;
ma_mask = false(size(green));
for i = 1:numel(ma_props)
    if ma_props(i).Area >= 2 && ma_props(i).Area <= 30 && ma_props(i).Eccentricity < 0.85
        ma_count = ma_count + 1;
        ma_mask(ma_cc.PixelIdxList{i}) = true;
    end
end

% 3. Hemorrhage Detection (Larger irregular dark blotches: > 30 px)
se_med = strel('disk', 10);
blackhat_med = imbothat(uint8(green), se_med);
hem_candidates = (double(blackhat_med) > 30) & search_zone;
hem_cc = bwconncomp(hem_candidates);
hem_props = regionprops(hem_cc, 'Area');
hem_count = 0;
hem_mask = false(size(green));
for i = 1:numel(hem_props)
    if hem_props(i).Area > 30 && hem_props(i).Area < 1000
        hem_count = hem_count + 1;
        hem_mask(hem_cc.PixelIdxList{i}) = true;
    end
end

% 4. Exudate Detection (Bright yellow-white deposits on green/intensity)
se_exudate = strel('disk', 8);
tophat_bright = imtophat(uint8(green), se_exudate);
exudate_candidates = (double(tophat_bright) > 35) & search_zone;
ex_cc = bwconncomp(exudate_candidates);
ex_props = regionprops(ex_cc, 'Area');
ex_count = 0;
ex_mask = false(size(green));
for i = 1:numel(ex_props)
    if ex_props(i).Area >= 5 && ex_props(i).Area < 1500
        ex_count = ex_count + 1;
        ex_mask(ex_cc.PixelIdxList{i}) = true;
    end
end

% 5. Neovascularization Detection (Abnormal tangled new vessels)
se_nv = strel('line', 9, 45);
nv_filter = imtophat(uint8(vessel_mask * 255), se_nv);
nv_candidates = bwareaopen(nv_filter > 100, 40);
nv_cc = bwconncomp(nv_candidates);
nv_count = nv_cc.NumObjects;

% Build return structure
lesions = struct();
lesions.microaneurysms = struct('count', ma_count, 'mask', ma_mask);
lesions.hemorrhages = struct('count', hem_count, 'mask', hem_mask);
lesions.exudates = struct('count', ex_count, 'mask', ex_mask);
lesions.neovascularization = struct('count', nv_count, 'present', nv_count > 0);
lesions.optic_disc = struct('row', disc_r, 'col', disc_c, 'mask', disc_mask);

end
