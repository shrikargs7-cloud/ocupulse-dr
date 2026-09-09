function lesions = lesion_quantification(img)
% Comprehensive lesion quantification using MATLAB
%
% Input: img - RGB fundus image
% Output: lesions - Structure with lesion data

% Convert to different color spaces
img_lab = rgb2lab(img);
img_hsv = rgb2hsv(img);
L = img_lab(:,:,1);
A = img_lab(:,:,2);
B = img_lab(:,:,3);
H = img_hsv(:,:,1);
S = img_hsv(:,:,2);
V = img_hsv(:,:,3);

% 1. Microaneurysms detection
[ma_count, ma_area, ma_locations] = detect_microaneurysms(A, B, L);

% 2. Exudates detection
[ex_count, ex_area, ex_locations] = detect_exudates(L, V);

% 3. Hemorrhages detection
[hem_count, hem_area, hem_locations] = detect_hemorrhages(A, B, H);

% 4. Neovascularization detection
[nv_count, nv_area, nv_locations] = detect_neovascularization(img, A, B);

% Compile results
lesions = struct();
lesions.microaneurysms = struct('count', ma_count, 'area', ma_area, 'locations', {ma_locations});
lesions.exudates = struct('count', ex_count, 'area', ex_area, 'locations', {ex_locations});
lesions.hemorrhages = struct('count', hem_count, 'area', hem_area, 'locations', {hem_locations});
lesions.neovascularization = struct('count', nv_count, 'area', nv_area, 'locations', {nv_locations});

% Calculate total lesion load
lesions.total_lesions = ma_count + ex_count + hem_count + nv_count;
lesions.total_lesion_area = ma_area + ex_area + hem_area + nv_area;

% Clinical severity based on lesions
lesions.severity = assess_lesion_severity(lesions);

end

function [count, area, locations] = detect_microaneurysms(A, B, L)
% Detect microaneurysms (small red spots)
% Normalize channels
A_norm = mat2gray(A);
B_norm = mat2gray(B);
L_norm = mat2gray(L);

% Microaneurysm candidates: dark in A, bright in B, and small
ma_score = (A_norm < 0.2) & (B_norm > 0.7) & (L_norm < 0.6);

% Morphological operations
se = strel('disk', 3);
ma_score = imopen(ma_score, se);
ma_score = imclose(ma_score, se);

% Remove small and large objects
ma_score = bwareaopen(ma_score, 5);
ma_score = bwareaopen(~ma_score, 100);
ma_score = ~ma_score;

% Label and count
labeled = bwlabel(ma_score);
count = max(labeled(:));
area = sum(ma_score(:));

% Extract locations
locations = [];
if count > 0
    props = regionprops(labeled, 'Centroid');
    locations = cat(1, props.Centroid);
end
end

function [count, area, locations] = detect_exudates(L, V)
% Detect exudates (bright yellow lesions)
L_norm = mat2gray(L);
V_norm = mat2gray(V);

% Exudate candidates: bright in L and V
ex_score = (L_norm > 0.7) & (V_norm > 0.6);

% Morphological operations
se = strel('disk', 5);
ex_score = imopen(ex_score, se);
ex_score = imclose(ex_score, se);

% Remove small objects
ex_score = bwareaopen(ex_score, 20);

% Label and count
labeled = bwlabel(ex_score);
count = max(labeled(:));
area = sum(ex_score(:));

% Extract locations
locations = [];
if count > 0
    props = regionprops(labeled, 'Centroid');
    locations = cat(1, props.Centroid);
end
end

function [count, area, locations] = detect_hemorrhages(A, B, H)
% Detect hemorrhages (dark red lesions)
A_norm = mat2gray(A);
B_norm = mat2gray(B);
H_norm = mat2gray(H);

% Hemorrhage candidates: dark in A, B, and H
hem_score = (A_norm < 0.25) & (B_norm < 0.4) & (H_norm < 0.3);

% Morphological operations
se = strel('disk', 5);
hem_score = imopen(hem_score, se);
hem_score = imclose(hem_score, se);

% Remove small objects
hem_score = bwareaopen(hem_score, 30);

% Label and count
labeled = bwlabel(hem_score);
count = max(labeled(:));
area = sum(hem_score(:));

% Extract locations
locations = [];
if count > 0
    props = regionprops(labeled, 'Centroid');
    locations = cat(1, props.Centroid);
end
end

function [count, area, locations] = detect_neovascularization(img, A, B)
% Detect neovascularization (abnormal new vessels)
% This is a simplified approach - real detection requires more complex analysis
A_norm = mat2gray(A);
B_norm = mat2gray(B);

% Neovascularization candidates: abnormal vessel patterns
% Look for tortuous, abnormal vessel structures
nv_score = (A_norm < 0.3) & (B_norm > 0.6);

% Enhance with vessel-like structures
img_gray = rgb2gray(img);
edges = edge(img_gray, 'canny');
nv_score = nv_score & edges;

% Morphological operations
se = strel('disk', 3);
nv_score = imopen(nv_score, se);
nv_score = imclose(nv_score, se);

% Remove small objects
nv_score = bwareaopen(nv_score, 10);

% Label and count
labeled = bwlabel(nv_score);
count = max(labeled(:));
area = sum(nv_score(:));

% Extract locations
locations = [];
if count > 0
    props = regionprops(labeled, 'Centroid');
    locations = cat(1, props.Centroid);
end
end

function severity = assess_lesion_severity(lesions)
% Assess DR severity based on lesions
ma = lesions.microaneurysms.count;
ex = lesions.exudates.count;
hem = lesions.hemorrhages.count;
nv = lesions.neovascularization.count;

% Apply ETDRS-like criteria
if nv > 0
    severity = 'Proliferative DR (PDR)';
elseif hem >= 20
    severity = 'Severe NPDR';
elseif ma >= 5 || ex >= 3 || (hem >= 5 && ma >= 2)
    severity = 'Moderate NPDR';
elseif ma >= 1
    severity = 'Mild NPDR';
else
    severity = 'No DR';
end
end