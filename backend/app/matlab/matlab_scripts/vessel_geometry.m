function geometry = vessel_geometry(vessel_mask, vessel_skeleton)
% Comprehensive vessel geometry analysis
%
% Input: vessel_mask - Binary vessel mask
%        vessel_skeleton - Skeletonized vessel image
% Output: geometry - Structure with all geometry metrics

% Ensure binary
vessel_mask = vessel_mask > 0;
vessel_skeleton = vessel_skeleton > 0;

% 1. Vessel density
geometry.density = sum(vessel_mask(:)) / numel(vessel_mask) * 100;

% 2. Vessel length
geometry.total_length = sum(vessel_skeleton(:));

% 3. Branching analysis
[branch_stats] = analyze_branching(vessel_skeleton);
geometry.branch_points = branch_stats.num_branches;
geometry.branching_density = branch_stats.branching_density;
geometry.avg_branch_angle = branch_stats.avg_angle;

% 4. Tortuosity analysis
geometry.tortuosity = compute_tortuosity(vessel_skeleton);

% 5. Vessel caliber analysis
[caliber_stats] = analyze_caliber(vessel_mask);
geometry.avg_caliber = caliber_stats.avg_caliber;
geometry.caliber_variance = caliber_stats.caliber_variance;

% 6. Fractal dimension (if needed)
geometry.fractal_dimension = compute_fractal_dimension(vessel_skeleton);

% 7. Complexity score
geometry.complexity_score = geometry.density * geometry.branching_density * geometry.tortuosity;

% 8. Clinical interpretation
geometry.interpretation = interpret_geometry(geometry);

end

function stats = analyze_branching(skeleton)
% Analyze branching patterns
% Find branch points (pixels with degree >= 3)
branch_points = find_branch_points(skeleton);
num_branches = size(branch_points, 1);

% Calculate branching density
total_pixels = sum(skeleton(:));
if total_pixels > 0
    branching_density = num_branches / total_pixels * 1000;
else
    branching_density = 0;
end

% Compute average branching angle
angles = compute_branch_angles(skeleton, branch_points);
if ~isempty(angles)
    avg_angle = mean(angles);
    std_angle = std(angles);
else
    avg_angle = 0;
    std_angle = 0;
end

stats.num_branches = num_branches;
stats.branching_density = branching_density;
stats.avg_angle = avg_angle;
stats.std_angle = std_angle;
stats.branch_points = branch_points;
end

function bp = find_branch_points(skeleton)
% Find branch points using 8-connectivity
[h, w] = size(skeleton);
bp = [];

for y = 2:h-1
    for x = 2:w-1
        if ~skeleton(y, x)
            continue;
        end
        
        % Count neighbors in 8-connectivity
        neighbors = 0;
        for dy = -1:1
            for dx = -1:1
                if dx == 0 && dy == 0
                    continue;
                end
                if skeleton(y+dy, x+dx)
                    neighbors = neighbors + 1;
                end
            end
        end
        
        if neighbors >= 3
            bp = [bp; x, y];
        end
    end
end
end

function angles = compute_branch_angles(skeleton, branch_points)
% Compute angles at branch points
angles = [];

for i = 1:size(branch_points, 1)
    x = branch_points(i, 1);
    y = branch_points(i, 2);
    
    % Find neighboring branches
    branches = find_branches(skeleton, x, y);
    
    if length(branches) < 2
        continue;
    end
    
    % Compute angles between all pairs of branches
    for j = 1:length(branches)
        for k = j+1:length(branches)
            v1 = branches{j} - [x, y];
            v2 = branches{k} - [x, y];
            
            % Normalize
            v1 = v1 / (norm(v1) + eps);
            v2 = v2 / (norm(v2) + eps);
            
            % Compute angle in degrees
            angle = acosd(max(min(dot(v1, v2), 1), -1));
            angles = [angles; angle];
        end
    end
end

% Remove angles < 10 degrees (likely noise)
angles = angles(angles > 10);
end

function branches = find_branches(skeleton, x, y)
% Find branches from a branch point
branches = {};
directions = [-1,-1; -1,0; -1,1; 0,-1; 0,1; 1,-1; 1,0; 1,1];

for d = 1:size(directions, 1)
    dx = directions(d, 1);
    dy = directions(d, 2);
    
    nx = x + dx;
    ny = y + dy;
    
    if nx >= 1 && nx <= size(skeleton, 2) && ...
       ny >= 1 && ny <= size(skeleton, 1) && ...
       skeleton(ny, nx)
        
        % Follow branch
        branch = follow_branch(skeleton, nx, ny, [x, y]);
        if ~isempty(branch)
            branches{end+1} = branch;
        end
    end
end
end

function branch = follow_branch(skeleton, x, y, prev)
% Follow a branch until endpoint or branch point
branch = [x - prev(1), y - prev(2)];
current = [x, y];
prev_pos = prev;

for step = 1:100  % Limit steps
    % Find neighbors
    neighbors = [];
    for dy = -1:1
        for dx = -1:1
            if dx == 0 && dy == 0
                continue;
            end
            nx = current(1) + dx;
            ny = current(2) + dy;
            if nx >= 1 && nx <= size(skeleton, 2) && ...
               ny >= 1 && ny <= size(skeleton, 1) && ...
               skeleton(ny, nx) && ...
               ~(nx == prev_pos(1) && ny == prev_pos(2))
                neighbors = [neighbors; nx, ny];
            end
        end
    end
    
    if isempty(neighbors)
        % Endpoint reached
        break;
    elseif size(neighbors, 1) > 1
        % Branch point reached
        break;
    else
        % Continue
        prev_pos = current;
        current = neighbors(1,:);
        branch = [branch; current(1) - prev_pos(1), current(2) - prev_pos(2)];
    end
end
end

function tortuosity = compute_tortuosity(skeleton)
% Compute tortuosity using arc/chord ratio
% Find all segments between endpoints
segments = find_segments(skeleton);

if isempty(segments)
    tortuosity = 1.0;
    return;
end

tortuosities = zeros(length(segments), 1);
for i = 1:length(segments)
    seg = segments{i};
    if length(seg) < 3
        continue;
    end
    
    % Arc length
    arc_len = 0;
    for j = 2:length(seg)
        arc_len = arc_len + norm(seg{j} - seg{j-1});
    end
    
    % Chord length
    chord_len = norm(seg{end} - seg{1});
    
    if chord_len > 0
        tortuosities(i) = arc_len / chord_len;
    end
end

% Remove outliers
tortuosities = tortuosities(tortuosities > 0);
if ~isempty(tortuosities)
    tortuosity = mean(tortuosities);
else
    tortuosity = 1.0;
end
end

function segments = find_segments(skeleton)
% Find all segments between endpoints
% Label connected components
labeled = bwlabel(skeleton);
num_components = max(labeled(:));

segments = {};
for comp = 1:num_components
    comp_mask = (labeled == comp);
    endpoints = find_endpoints(comp_mask);
    
    % For each pair of endpoints, find path
    for i = 1:size(endpoints, 1)
        for j = i+1:size(endpoints, 1)
            path = find_path(comp_mask, endpoints(i,:), endpoints(j,:));
            if ~isempty(path)
                segments{end+1} = path;
            end
        end
    end
end
end

function endpoints = find_endpoints(skeleton)
% Find endpoints (degree = 1)
[h, w] = size(skeleton);
endpoints = [];

for y = 2:h-1
    for x = 2:w-1
        if ~skeleton(y, x)
            continue;
        end
        
        % Count neighbors
        neighbors = 0;
        for dy = -1:1
            for dx = -1:1
                if dx == 0 && dy == 0
                    continue;
                end
                if skeleton(y+dy, x+dx)
                    neighbors = neighbors + 1;
                end
            end
        end
        
        if neighbors == 1
            endpoints = [endpoints; x, y];
        end
    end
end
end

function path = find_path(skeleton, start, target)
% Find shortest path between two points
% Simple BFS implementation
[h, w] = size(skeleton);
visited = false(h, w);
queue = {start};
visited(start(2), start(1)) = true;
parent = containers.Map();

while ~isempty(queue)
    current = queue{1};
    queue(1) = [];
    
    if current(1) == target(1) && current(2) == target(2)
        % Reconstruct path
        path = {};
        while ~(current(1) == start(1) && current(2) == start(2))
            path{end+1} = current;
            current = parent([current(1), current(2)]);
        end
        path{end+1} = start;
        path = fliplr(path);
        return;
    end
    
    % Check neighbors
    for dy = -1:1
        for dx = -1:1
            if dx == 0 && dy == 0
                continue;
            end
            nx = current(1) + dx;
            ny = current(2) + dy;
            if nx >= 1 && nx <= w && ny >= 1 && ny <= h && ...
               skeleton(ny, nx) && ~visited(ny, nx)
                visited(ny, nx) = true;
                queue{end+1} = [nx, ny];
                parent([nx, ny]) = current;
            end
        end
    end
end

path = [];  % No path found
end

function stats = analyze_caliber(vessel_mask)
% Analyze vessel caliber (thickness)
% Use distance transform to estimate caliber
dist = bwdist(~vessel_mask);
calibers = dist(vessel_mask);

if ~isempty(calibers)
    stats.avg_caliber = mean(calibers);
    stats.caliber_variance = var(calibers);
    stats.max_caliber = max(calibers);
    stats.min_caliber = min(calibers);
    stats.median_caliber = median(calibers);
else
    stats.avg_caliber = 0;
    stats.caliber_variance = 0;
    stats.max_caliber = 0;
    stats.min_caliber = 0;
    stats.median_caliber = 0;
end
end

function fd = compute_fractal_dimension(skeleton)
% Compute fractal dimension (simplified)
% Use box-counting
skeleton = skeleton > 0;
[height, width] = size(skeleton);
max_dim = max(height, width);

box_sizes = [];
for k = 1:floor(log2(max_dim))
    box_size = 2^k;
    if box_size < max_dim
        box_sizes = [box_sizes, box_size];
    end
end

counts = zeros(size(box_sizes));
for i = 1:length(box_sizes)
    counts(i) = count_boxes(skeleton, box_sizes(i));
end

valid = counts > 0;
if sum(valid) < 3
    fd = 1.0;
    return;
end

log_sizes = log(1 ./ box_sizes(valid));
log_counts = log(counts(valid));
p = polyfit(log_sizes, log_counts, 1);
fd = p(1);
end

function interpretation = interpret_geometry(geometry)
% Clinical interpretation of geometry metrics
score = 0;

% Fractal dimension
if isfield(geometry, 'fractal_dimension')
    if geometry.fractal_dimension > 1.75
        score = score + 3;
    elseif geometry.fractal_dimension > 1.65
        score = score + 2;
    elseif geometry.fractal_dimension > 1.55
        score = score + 1;
    end
end

% Density
if geometry.density > 15
    score = score + 2;
elseif geometry.density > 10
    score = score + 1;
end

% Tortuosity
if geometry.tortuosity > 1.5
    score = score + 2;
elseif geometry.tortuosity > 1.3
    score = score + 1;
end

% Branching density
if geometry.branching_density > 5
    score = score + 2;
elseif geometry.branching_density > 3
    score = score + 1;
end

% Interpret
if score >= 7
    interpretation = 'High risk - Advanced vascular changes consistent with proliferative DR';
elseif score >= 5
    interpretation = 'Moderate risk - Significant changes consistent with moderate/severe NPDR';
elseif score >= 3
    interpretation = 'Borderline - Mild changes, monitor closely';
else
    interpretation = 'Normal - Vascular geometry within normal limits';
end
end