function result = simulate_pipeline(patient_volume, bandwidth_mbps, ...
                                    processing_throughput, review_capacity, ...
                                    operating_hours)
% Simulate telemedicine screening pipeline using Simulink
%
% Inputs:
%   patient_volume - Annual patient volume (e.g., 100,000)
%   bandwidth_mbps - Network bandwidth in Mbps
%   processing_throughput - Images processed per second
%   review_capacity - Number of reviewers
%   operating_hours - Hours per day
%
% Output: result - Structure with simulation results

% Create Simulink model parameters
params = struct();
params.patient_volume = patient_volume;
params.bandwidth_mbps = bandwidth_mbps;
params.processing_throughput = processing_throughput;
params.review_capacity = review_capacity;
params.operating_hours = operating_hours;
params.working_days_per_year = 260;

% Calculate daily throughput
daily_throughput = processing_throughput * 3600 * operating_hours;
images_per_day = min(daily_throughput, bandwidth_mbps * 1000 / 10);  % Assume 10MB per image

% Annual capacity
annual_capacity = images_per_day * params.working_days_per_year;

% Backlog calculation
backlog = max(0, patient_volume - annual_capacity);
backlog_after_year = backlog;

% Cost calculation
cost_per_image = 5.0;  % USD
review_cost_per_image = 2.0;  % USD
total_cost = patient_volume * (cost_per_image + review_cost_per_image / review_capacity);

% Optimized parameters
optimized_params = params;
if backlog > 0
    % Need to increase capacity
    required_throughput = patient_volume / (params.working_days_per_year * 3600 * operating_hours);
    optimized_params.processing_throughput = max(required_throughput, processing_throughput);
    optimized_params.review_capacity = ceil(patient_volume / (params.working_days_per_year * 100));  % 100 images per reviewer per day
    optimized_params.bandwidth_mbps = max(patient_volume * 10 / (params.working_days_per_year * 3600 * operating_hours), bandwidth_mbps);
end

% Recommendations
recommendations = {};
if backlog > 0
    recommendations{end+1} = sprintf('Increase processing throughput to %.2f images/sec', required_throughput);
    recommendations{end+1} = sprintf('Increase reviewer capacity to %d reviewers', optimized_params.review_capacity);
    recommendations{end+1} = sprintf('Increase bandwidth to %.2f Mbps', optimized_params.bandwidth_mbps);
else
    recommendations{end+1} = 'Current capacity sufficient for patient volume';
    recommendations{end+1} = 'Consider expanding service to more regions';
end

% Results
result = struct();
result.total_cost = total_cost;
result.cost_per_patient = total_cost / patient_volume;
result.throughput_per_day = images_per_day;
result.backlog_after_year = backlog_after_year;
result.optimized_params = optimized_params;
result.recommendations = {recommendations};
result.patient_volume = patient_volume;
result.annual_capacity = annual_capacity;

% Additional metrics
result.utilization_rate = patient_volume / annual_capacity;
if result.utilization_rate > 0.9
    recommendations{end+1} = 'System utilization > 90% - Consider scaling up';
elseif result.utilization_rate < 0.5
    recommendations{end+1} = 'System utilization < 50% - Consider reducing capacity to optimize costs';
end

end