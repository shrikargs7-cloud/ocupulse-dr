function viz = explainability_viz(img, grading, features, lesions)
% Generate explainability visualizations for the report
%
% Input: img - Original fundus image
%        grading - Grading structure
%        features - Feature structure
%        lesions - Lesion structure
% Output: viz - Structure with visualization paths

% Create figures directory if it doesn't exist
if ~exist('matlab_plots', 'dir')
    mkdir('matlab_plots');
end

% 1. Feature importance bar chart
fig1 = figure('Visible', 'off', 'Position', [100, 100, 800, 600]);
feature_names = {'Fractal Dim', 'Vessel Density', 'Tortuosity', 'Microaneurysms', 'Exudates', 'Hemorrhages'};
feature_values = [features.fractal_dimension, features.density, ...
                  features.tortuosity, lesions.microaneurysms.count, ...
                  lesions.exudates.count, lesions.hemorrhages.count];

% Normalize for visualization
feature_values_norm = feature_values / max(feature_values);
bar(feature_values_norm);
set(gca, 'XTickLabel', feature_names);
xtickangle(45);
title('Feature Importance for DR Grading');
ylabel('Normalized Value');
colormap('jet');
grid on;

% Save
saveas(fig1, 'matlab_plots/feature_importance.png');
close(fig1);

% 2. Lesion distribution
fig2 = figure('Visible', 'off', 'Position', [100, 100, 600, 600]);
lesion_types = {'Microaneurysms', 'Exudates', 'Hemorrhages', 'Neovascularization'};
lesion_counts = [lesions.microaneurysms.count, lesions.exudates.count, ...
                 lesions.hemorrhages.count, lesions.neovascularization.count];

% Only include lesions with count > 0
valid = lesion_counts > 0;
if any(valid)
    pie(lesion_counts(valid), lesion_types(valid));
    title('Lesion Distribution');
else
    text(0.5, 0.5, 'No Lesions Detected', 'HorizontalAlignment', 'center');
    title('Lesion Distribution');
end

% Save
saveas(fig2, 'matlab_plots/lesion_distribution.png');
close(fig2);

% 3. Vessel overlay on original image
fig3 = figure('Visible', 'off', 'Position', [100, 100, 800, 600]);

% Get vessel mask (would need vessel segmentation)
% For demo, we use a placeholder
subplot(1,2,1);
imshow(img);
title('Original Fundus Image');

subplot(1,2,2);
% Overlay vessel mask (in red) on image
img_overlay = img;
% Placeholder - in practice, use actual vessel mask
imshow(img_overlay);
title('Vessel Overlay');

% Save
saveas(fig3, 'matlab_plots/vessel_overlay.png');
close(fig3);

% 4. Risk assessment dashboard
fig4 = figure('Visible', 'off', 'Position', [100, 100, 1000, 700]);

% Create 2x3 grid of subplots
subplot(2,3,1);
metrics = [features.fractal_dimension, features.density, features.tortuosity];
bar(metrics);
set(gca, 'XTickLabel', {'Fractal Dim', 'Density', 'Tortuosity'});
title('Geometric Metrics');
ylabel('Value');

subplot(2,3,2);
% Radar chart for lesion profile
lesion_metrics = [lesions.microaneurysms.count, lesions.exudates.count, ...
                  lesions.hemorrhages.count, lesions.neovascularization.count];
max_vals = [10, 10, 20, 5];
plot(radar_plot(lesion_metrics, max_vals));
title('Lesion Profile');
legend({'Current', 'Threshold'});

subplot(2,3,3);
% Confidence gauge
confidence = grading.confidence;
color = 'green';
if confidence < 0.5
    color = 'red';
elseif confidence < 0.7
    color = 'yellow';
end
gauge = [confidence*100, (1-confidence)*100];
pie(gauge, {'Confidence', 'Uncertainty'});
title('Prediction Confidence');
colormap([color; 'lightgray']);

subplot(2,3,4);
% Severity heatmap
grades = {'No DR', 'Mild', 'Moderate', 'Severe', 'PDR'};
probabilities = [0.8, 0.1, 0.05, 0.03, 0.02]; % Placeholder
bar(probabilities);
set(gca, 'XTickLabel', grades);
xtickangle(45);
title('Severity Probability Distribution');
ylabel('Probability');
ylim([0, 1]);

subplot(2,3,5);
% Scatter plot of key metrics
scatter(features.fractal_dimension, features.density, 100, 'filled');
hold on;
scatter(1.65, 10, 100, 'red', 'filled'); % Threshold reference
xlabel('Fractal Dimension');
ylabel('Vessel Density');
title('Geometry vs. Density');
legend({'Current', 'Threshold'});
grid on;

subplot(2,3,6);
% Text summary
text_str = sprintf(['DR Grade: %s\n', ...
                    'Confidence: %.1f%%\n', ...
                    'Referable DR: %s\n', ...
                    'Total Lesions: %d\n', ...
                    'Recommendation: %s'], ...
                   grading.grade_label, ...
                   grading.confidence*100, ...
                   iff(grading.is_referable, 'Yes', 'No'), ...
                   lesions.total_lesions, ...
                   grading.recommendation);
text(0.1, 0.5, text_str, 'FontSize', 12, 'VerticalAlignment', 'middle');
axis off;
title('Clinical Summary');

% Save
saveas(fig4, 'matlab_plots/risk_dashboard.png');
close(fig4);

% Return visualization paths
viz = struct();
viz.feature_importance = 'matlab_plots/feature_importance.png';
viz.lesion_distribution = 'matlab_plots/lesion_distribution.png';
viz.vessel_overlay = 'matlab_plots/vessel_overlay.png';
viz.risk_dashboard = 'matlab_plots/risk_dashboard.png';

end

function result = iff(condition, true_val, false_val)
% Simple conditional function
if condition
    result = true_val;
else
    result = false_val;
end
end

function data = radar_plot(values, max_vals)
% Simplified radar plot for lesion profile
n = length(values);
angles = linspace(0, 2*pi, n+1);
angles = angles(1:end-1);

% Normalize values
norm_vals = values ./ max_vals;

% Create radar coordinates
x = norm_vals .* cos(angles);
y = norm_vals .* sin(angles);

% Complete the radar
x = [x, x(1)];
y = [y, y(1)];

% Add threshold reference
thresh = 0.8 * ones(1, n);
x_thresh = thresh .* cos(angles);
y_thresh = thresh .* sin(angles);
x_thresh = [x_thresh, x_thresh(1)];
y_thresh = [y_thresh, y_thresh(1)];

data = plot(x, y, x_thresh, y_thresh);
end