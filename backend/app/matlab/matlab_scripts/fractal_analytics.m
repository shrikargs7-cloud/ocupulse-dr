function [fractal_dim, stats] = fractal_analysis(vessel_image)
% Fractal Dimension Analysis using Box-Counting Method
% D = lim(ε→0) log(N(ε)) / log(1/ε)
%
% Input: vessel_image - Binary image of vessel segmentation
% Output: fractal_dim - Fractal dimension
%         stats - Additional statistics

% Ensure binary
vessel_image = vessel_image > 0;

% Get image size
[height, width] = size(vessel_image);
max_dim = max(height, width);

% Define box sizes (powers of 2)
box_sizes = [];
for k = 1:floor(log2(max_dim))
    box_size = 2^k;
    if box_size < max_dim
        box_sizes = [box_sizes, box_size];
    end
end

% Count boxes for each size
counts = zeros(size(box_sizes));
for i = 1:length(box_sizes)
    box_size = box_sizes(i);
    counts(i) = count_boxes(vessel_image, box_size);
end

% Remove zero counts
valid = counts > 0;
box_sizes = box_sizes(valid);
counts = counts(valid);

if length(box_sizes) < 3
    fractal_dim = 1.0;
    stats = struct('error', 'Insufficient data for fractal analysis');
    return;
end

% Linear regression in log-log space
log_sizes = log(1 ./ box_sizes);
log_counts = log(counts);

% Fit line using polyfit
p = polyfit(log_sizes, log_counts, 1);
fractal_dim = p(1);

% Calculate R-squared
fitted = polyval(p, log_sizes);
ss_res = sum((log_counts - fitted).^2);
ss_tot = sum((log_counts - mean(log_counts)).^2);
r_squared = 1 - ss_res / ss_tot;

% Additional statistics
stats = struct();
stats.fractal_dimension = fractal_dim;
stats.r_squared = r_squared;
stats.box_sizes = box_sizes;
stats.counts = counts;
stats.log_sizes = log_sizes;
stats.log_counts = log_counts;
stats.intercept = p(2);

% Confidence intervals
n = length(log_sizes);
se = sqrt(sum((log_counts - fitted).^2) / (n - 2));
t_val = tinv(0.975, n - 2);
stats.slope_ci = [fractal_dim - t_val * se / sqrt(sum((log_sizes - mean(log_sizes)).^2)), ...
                  fractal_dim + t_val * se / sqrt(sum((log_sizes - mean(log_sizes)).^2))];

% Interpret fractal dimension
if fractal_dim < 1.5
    stats.interpretation = 'Low complexity - Normal vascular structure';
elseif fractal_dim < 1.65
    stats.interpretation = 'Moderate complexity - Borderline changes';
elseif fractal_dim < 1.75
    stats.interpretation = 'High complexity - Possible DR progression';
else
    stats.interpretation = 'Very high complexity - Advanced DR changes';
end

end

function count = count_boxes(image, box_size)
% Count boxes containing vessel pixels
[height, width] = size(image);
count = 0;

for i = 1:box_size:height
    for j = 1:box_size:width
        % Get box region
        row_end = min(i + box_size - 1, height);
        col_end = min(j + box_size - 1, width);
        box = image(i:row_end, j:col_end);
        
        % Check if box contains any vessel pixels
        if any(box(:))
            count = count + 1;
        end
    end
end
end