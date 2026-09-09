function grading = severity_grading(features, lesions)
% DR Severity Grading based on International Clinical DR Scale
%
% Input: features - Structure with geometric features
%        lesions - Structure with lesion counts
% Output: grading - Structure with grade and confidence

% Extract features
fractal_dim = features.fractal_dimension;
density = features.density;
tortuosity = features.tortuosity;

% Extract lesion counts
ma = lesions.microaneurysms.count;
ex = lesions.exudates.count;
hem = lesions.hemorrhages.count;
nv = lesions.neovascularization.count;

% Initialize grade
grade = 0;
grade_label = 'No DR';
criteria = {};
confidence = 0.0;

% Clinical criteria
if nv > 0
    % Neovascularization indicates PDR
    grade = 4;
    grade_label = 'Proliferative DR (PDR)';
    criteria = {'Neovascularization present', 'Abnormal vessel proliferation'};
    confidence = 0.95;
    
elseif hem >= 20 || (hem >= 10 && ma >= 5)
    % Severe NPDR
    grade = 3;
    grade_label = 'Severe NPDR';
    criteria = {sprintf('%d hemorrhages detected', hem), 'Severe vascular changes'};
    confidence = 0.90;
    
elseif ma >= 5 || ex >= 3 || hem >= 5
    % Moderate NPDR
    grade = 2;
    grade_label = 'Moderate NPDR';
    criteria = {sprintf('%d microaneurysms, %d exudates, %d hemorrhages', ma, ex, hem)};
    confidence = 0.85;
    
elseif ma >= 1
    % Mild NPDR
    grade = 1;
    grade_label = 'Mild NPDR';
    criteria = {sprintf('%d microaneurysm(s) detected', ma)};
    confidence = 0.80;
    
else
    % No DR
    grade = 0;
    grade_label = 'No DR';
    criteria = {'No lesions detected', 'Normal vascular geometry'};
    confidence = 0.75;
end

% Adjust confidence based on geometry
if fractal_dim > 1.75
    confidence = min(confidence + 0.05, 1.0);
    criteria{end+1} = 'High fractal dimension indicating vascular complexity';
elseif fractal_dim > 1.65
    confidence = min(confidence + 0.02, 1.0);
end

if tortuosity > 1.5
    confidence = min(confidence + 0.03, 1.0);
    criteria{end+1} = 'Increased vessel tortuosity';
end

% Grading
grading = struct();
grading.grade = grade;
grading.grade_label = grade_label;
grading.confidence = confidence;
grading.criteria = {criteria};
grading.is_referable = grade >= 2;
grading.is_vision_threatening = grade >= 4;
grading.recommendation = generate_recommendation(grade);

end

function recommendation = generate_recommendation(grade)
% Generate clinical recommendation based on grade
switch grade
    case 0
        recommendation = 'Routine screening - No DR detected. Continue annual examinations.';
    case 1
        recommendation = 'Mild NPDR - Monitor annually. Control blood glucose and blood pressure.';
    case 2
        recommendation = 'Moderate NPDR - Refer to ophthalmologist. Schedule 6-month follow-up.';
    case 3
        recommendation = 'Severe NPDR - Urgent referral to ophthalmologist. Consider treatment.';
    case 4
        recommendation = 'PDR - Immediate referral to retinal specialist. Consider laser treatment.';
    otherwise
        recommendation = 'Unable to grade - Please consult with a specialist.';
end
end