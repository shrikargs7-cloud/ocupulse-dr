function result = analyze_retina(img)
% Analyze retinal image with MATLAB
%
% Input: img - RGB image
% Output: result - Structure with analysis results

% Convert to double
img = double(img) / 255;

% Extract color channels
R = img(:,:,1);
G = img(:,:,2);
B = img(:,:,3);

% 1. Quality assessment
quality = assess_quality(img);

% 2. Vessel extraction
[ves_mask, ves_skel] = extract_vessels(G);

% 3. Fractal dimension
fractal_dim = compute_fractal_dim(ves_skel);

% 4. Lesion detection
lesions = detect_lesions(img);

% 5. Geometry analysis
geometry = analyze_geometry(ves_mask, ves_skel);

% 6. DR grading
grading = grade_dr(lesions, fractal_dim);

% Compile results
result.quality = quality;
result.vessel_mask = ves_mask;
result.vessel_skeleton = ves_skel;
result.fractal_dimension = fractal_dim;
result.lesions = lesions;
result.geometry = geometry;
result.grading = grading;
result.summary = generate_summary(grading, lesions, geometry);

end

function quality = assess_quality(img)
    % Quality assessment
    gray = rgb2gray(img);
    
    % Focus (Laplacian variance)
    lap_var = var(double(imfilter(gray, fspecial('laplacian'))));
    quality.focus_score = min(lap_var / 1000, 1.0);
    
    % Illumination
    mean_int = mean(gray(:));
    quality.illumination_score = 1 - abs(mean_int - 0.5) * 2;
    
    % Overall
    quality.score = (quality.focus_score + quality.illumination_score) / 2;
    
    if quality.score > 0.6
        quality.grade = 'Good';
    elseif quality.score > 0.4
        quality.grade = 'Borderline';
    else
        quality.grade = 'Reject';
    end
end

function [ves_mask, ves_skel] = extract_vessels(G)
    % Extract vessels using Frangi filter
    % Preprocess
    G = imadjust(G);
    
    % Frangi filter
    options = struct('FrangiScaleRange', [1 3], ...
                     'FrangiScaleRatio', 0.5, ...
                     'FrangiBetaOne', 0.5, ...
                     'FrangiBetaTwo', 15);
    
    [~, ves_mask] = FrangiFilter2D(G, options);
    
    % Threshold
    ves_mask = ves_mask > 0.3;
    
    % Skeletonize
    ves_skel = bwmorph(ves_mask, 'skel', Inf);
end

function fractal_dim = compute_fractal_dim(skel)
    % Compute fractal dimension using box-counting
    [N, counts] = boxcount(skel);
    
    % Linear regression in log-log space
    x = log(1./N);
    y = log(counts(counts > 0));
    p = polyfit(x, y, 1);
    fractal_dim = p(1);
end

function lesions = detect_lesions(img)
    % Detect lesions using morphological operations
    
    % Convert to LAB
    lab = rgb2lab(img);
    L = lab(:,:,1);
    A = lab(:,:,2);
    B = lab(:,:,3);
    
    % Microaneurysms (red spots)
    microaneurysms = detect_microaneurysms(A, B);
    
    % Exudates (bright yellow)
    exudates = detect_exudates(L);
    
    % Hemorrhages (dark red)
    hemorrhages = detect_hemorrhages(A);
    
    lesions.microaneurysms = microaneurysms.count;
    lesions.exudates = exudates.count;
    lesions.hemorrhages = hemorrhages.count;
    lesions.total_lesions = lesions.microaneurysms + lesions.exudates + lesions.hemorrhages;
end

function micro = detect_microaneurysms(A, B)
    % Detect microaneurysms in AB channels
    % Red spots appear as dark in A and bright in B
    micro_map = (A < 20) & (B > 180);
    micro_map = imopen(micro_map, strel('disk', 3));
    [~, num] = bwlabel(micro_map);
    micro.count = num;
    micro.area = sum(micro_map(:));
end

function exudates = detect_exudates(L)
    % Detect exudates in L channel
    % Exudates appear bright
    exudate_map = L > 0.8;
    exudate_map = imopen(exudate_map, strel('disk', 5));
    [~, num] = bwlabel(exudate_map);
    exudates.count = num;
    exudates.area = sum(exudate_map(:));
end

function hemo = detect_hemorrhages(A)
    % Detect hemorrhages in A channel
    % Hemorrhages appear dark
    hemo_map = A < 20;
    hemo_map = imopen(hemo_map, strel('disk', 5));
    [~, num] = bwlabel(hemo_map);
    hemo.count = num;
    hemo.area = sum(hemo_map(:));
end

function geometry = analyze_geometry(ves_mask, ves_skel)
    % Analyze vessel geometry
    % Density
    geometry.density = sum(ves_mask(:)) / numel(ves_mask) * 100;
    
    % Tortuosity
    geometry.tortuosity = compute_tortuosity(ves_skel);
    
    % Branching
    geometry.branching_angle = compute_branching_angle(ves_skel);
end

function tort = compute_tortuosity(skel)
    % Compute tortuosity from skeleton
    % Simplified: uses arc/chord ratio
    [y, x] = find(skel);
    if length(x) < 3
        tort = 1.0;
        return;
    end
    
    % Fit polynomial
    p = polyfit(x, y, 2);
    y_fit = polyval(p, x);
    
    % Arc length
    arc_len = sum(sqrt(diff(x).^2 + diff(y).^2));
    
    % Chord length
    chord_len = sqrt((x(end)-x(1))^2 + (y(end)-y(1))^2);
    
    tort = arc_len / (chord_len + eps);
end

function angle = compute_branching_angle(skel)
    % Compute average branching angle
    bp = bwmorph(skel, 'branchpoints');
    [y, x] = find(bp);
    
    if isempty(x)
        angle = 0;
        return;
    end
    
    angles = [];
    for i = 1:length(x)
        % Find neighbors
        [ny, nx] = find(skel(max(1,y(i)-5):min(size(skel,1),y(i)+5), ...
                            max(1,x(i)-5):min(size(skel,2),x(i)+5)));
        if length(nx) > 2
            % Compute pairwise angles
            for j = 1:length(nx)
                for k = j+1:length(nx)
                    v1 = [nx(j), ny(j)] - [x(i), y(i)];
                    v2 = [nx(k), ny(k)] - [x(i), y(i)];
                    angle = atan2d(abs(cross([v1,0], [v2,0])), dot(v1, v2));
                    angles = [angles; angle];
                end
            end
        end
    end
    
    angle = mean(angles) if ~isempty(angles) else 0;
end

function grading = grade_dr(lesions, fractal_dim)
    % Grade DR severity based on lesions and geometry
    
    total_lesions = lesions.total_lesions;
    micro = lesions.microaneurysms;
    exu = lesions.exudates;
    hemo = lesions.hemorrhages;
    
    if total_lesions == 0 && fractal_dim < 1.6
        grade = 0;
        label = 'No DR';
    elseif micro > 0 && exu == 0 && hemo == 0
        grade = 1;
        label = 'Mild NPDR';
    elseif micro >= 5 || exu >= 3 || hemo >= 5
        grade = 2;
        label = 'Moderate NPDR';
    elseif hemo >= 20 || fractal_dim > 1.75
        grade = 3;
        label = 'Severe NPDR';
    else
        grade = 4;
        label = 'PDR';
    end
    
    grading.grade = grade;
    grading.label = label;
    grading.is_referable = grade >= 2;
    grading.is_vision_threatening = grade >= 4;
end

function summary = generate_summary(grading, lesions, geometry)
    % Generate clinical summary
    summary = sprintf('DR Grade: %s (Level %d)\n', grading.label, grading.grade);
    summary = [summary, sprintf('Lesions: %d (MA: %d, Ex: %d, Hem: %d)\n', ...
                lesions.total_lesions, lesions.microaneurysms, ...
                lesions.exudates, lesions.hemorrhages)];
    summary = [summary, sprintf('Vessel Density: %.1f%%\n', geometry.density)];
    summary = [summary, sprintf('Fractal Dimension: %.3f\n', geometry.fractal_dimension)];
    
    if grading.is_referable
        summary = [summary, 'WARNING: Referable DR detected - Immediate specialist referral recommended'];
    else
        summary = [summary, 'No referable DR detected - Routine monitoring advised'];
    end
end