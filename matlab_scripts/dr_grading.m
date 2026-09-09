function results = analyze_dr(image_path, patient_id, age, gender, diabetes_duration)
% Main entry point for DR analysis
%
% Input:
%   image_path - Path to fundus image
%   patient_id - Patient identifier
%   age - Patient age
%   gender - Patient gender
%   diabetes_duration - Years since diabetes diagnosis
%
% Output:
%   results - Complete analysis results

% Read image
img = imread(image_path);

% 1. Quality Assessment
quality = assess_quality(img);

if strcmp(quality.grade, 'Reject')
    results = struct();
    results.quality = quality;
    results.error = 'Image quality insufficient for analysis';
    results.recommendation = 'Please recapture image with better quality';
    return;
end

% 2. Image Enhancement (using MATLAB's built-in functions)
img_enhanced = enhance_image(img);

% 3. Vessel Extraction
[ves_mask, ves_skel] = extract_vessels(img_enhanced);

% 4. Fractal Analysis
[fractal_dim, fractal_stats] = fractal_analysis(ves_skel);

% 5. Geometry Analysis
geometry = vessel_geometry(ves_mask, ves_skel);

% 6. Lesion Detection
lesions = lesion_quantification(img_enhanced);

% 7. DR Grading
features = struct();
features.fractal_dimension = fractal_dim;
features.density = geometry.density;
features.tortuosity = geometry.tortuosity;
features.branching_angle = geometry.avg_branch_angle;
features.complexity_score = geometry.complexity_score;
features.interpretation = geometry.interpretation;

grading = severity_grading(features, lesions);

% 8. Explainability Visualizations
viz = explainability_viz(img, grading, features, lesions);

% 9. Generate Report
patient_info = struct();
patient_info.patient_id = patient_id;
patient_info.age = age;
patient_info.gender = gender;
patient_info.diabetes_duration = diabetes_duration;

results = struct();
results.patient_id = patient_id;
results.age = age;
results.gender = gender;
results.diabetes_duration = diabetes_duration;
results.quality = quality;
results.vessel_mask = ves_mask;
results.vessel_skeleton = ves_skel;
results.fractal_dimension = fractal_dim;
results.fractal_stats = fractal_stats;
results.features = features;
results.geometry = geometry;
results.lesions = lesions;
results.grading = grading;
results.viz = viz;

% Generate report
report_dir = 'reports';
if ~exist(report_dir, 'dir')
    mkdir(report_dir);
end
results.report = report_generation(results, report_dir);

% Display summary
disp('========================================');
disp('DR ANALYSIS COMPLETE');
disp('========================================');
disp(['Patient: ', patient_id]);
disp(['DR Grade: ', grading.grade_label, ' (Level ', num2str(grading.grade), ')']);
disp(['Confidence: ', num2str(grading.confidence * 100), '%']);
disp(['Referable DR: ', iff(grading.is_referable, 'Yes', 'No')]);
disp(['Total Lesions: ', num2str(lesions.total_lesions)]);
disp(['Fractal Dimension: ', num2str(fractal_dim)]);
disp(['Recommendation: ', grading.recommendation]);
disp('========================================');

end

function img_enhanced = enhance_image(img)
% Enhance image quality
% Convert to double
img_double = double(img) / 255;

% Apply CLAHE
if size(img_double, 3) == 3
    % Color image
    lab = rgb2lab(img_double);
    L = lab(:,:,1);
    
    % Apply CLAHE to L channel
    L_enhanced = adapthisteq(L, 'NumTiles', [8, 8], 'ClipLimit', 0.02);
    
    % Merge
    lab_enhanced = cat(3, L_enhanced, lab(:,:,2), lab(:,:,3));
    img_enhanced = lab2rgb(lab_enhanced);
else
    % Grayscale
    img_enhanced = adapthisteq(img_double, 'NumTiles', [8, 8], 'ClipLimit', 0.02);
end

% Convert back to uint8
img_enhanced = uint8(img_enhanced * 255);
end