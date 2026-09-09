function [quality, enhanced_img] = quality_assessment(img)
% QUALITY_ASSESSMENT Evaluates retinal fundus image quality & enhances borderline scans
%
% Inputs:
%   img - RGB or grayscale retinal fundus image
%
% Outputs:
%   quality - Structure containing:
%       score: Overall quality score (0.0 to 1.0)
%       grade: 'Good', 'Borderline', or 'Reject'
%       focus: Laplacian variance focus metric
%       illumination: Illumination uniformity score
%       fov: Field of view coverage ratio
%       recommendations: Recapture or enhancement feedback
%   enhanced_img - Contrast & illumination enhanced image if borderline

if size(img, 3) == 3
    gray = rgb2gray(img);
    green = img(:, :, 2);
else
    gray = img;
    green = img;
end

% 1. Focus Metric: Variance of Laplacian
laplacian_kernel = [0 1 0; 1 -4 1; 0 1 0];
lap_img = conv2(double(gray), laplacian_kernel, 'same');
focus_var = var(lap_img(:));
focus_score = min(1.0, focus_var / 500.0);

% 2. Illumination Score: Deviation from optimal mean (0.45-0.55)
mean_illum = mean(double(gray(:))) / 255.0;
illumination_score = max(0.0, 1.0 - abs(mean_illum - 0.5) * 2.0);

% 3. Field of View (FOV) Mask Detection
fov_mask = gray > 15;
fov_score = sum(fov_mask(:)) / numel(fov_mask);

% 4. Weighted Composite Quality Score
score = (0.45 * focus_score) + (0.35 * illumination_score) + (0.20 * fov_score);

% 5. Clinical Classification
if score >= 0.60
    grade = 'Good';
    recommendations = 'Image quality adequate for automated DR screening.';
    enhanced_img = img;
elseif score >= 0.40
    grade = 'Borderline';
    recommendations = 'Borderline illumination/focus. Automated CLAHE enhancement applied.';
    % Apply CLAHE enhancement
    if size(img, 3) == 3
        lab = rgb2lab(img);
        lab(:, :, 1) = adapthisteq(lab(:, :, 1) / 100.0, 'ClipLimit', 0.02) * 100.0;
        enhanced_img = lab2rgb(lab);
    else
        enhanced_img = adapthisteq(img, 'ClipLimit', 0.02);
    end
else
    grade = 'Reject';
    recommendations = 'Image ungradeable. Recapture required with adequate pupil dilation and centered fixation.';
    enhanced_img = img;
end

quality = struct();
quality.score = score;
quality.grade = grade;
quality.focus = focus_score;
quality.illumination = illumination_score;
quality.fov = fov_score;
quality.recommendations = recommendations;

end
