function fd = fractal_dimension(binary_skeleton)
% FRACTAL_DIMENSION Computes box-counting fractal dimension of vascular skeleton
%
% Inputs:
%   binary_skeleton - 2D logical image of 1-pixel wide vessel skeleton
%
% Output:
%   fd - Estimated fractal dimension (typically between 1.30 and 1.75 for retina)

if ~islogical(binary_skeleton)
    binary_skeleton = binary_skeleton > 0;
end

[height, width] = size(binary_skeleton);
max_dim = max(height, width);

% Pad to power of 2
p = 2^ceil(log2(max_dim));
padded = false(p, p);
padded(1:height, 1:width) = binary_skeleton;

% Box sizes (powers of 2: 2, 4, 8, 16, 32, 64, 128)
box_sizes = [2, 4, 8, 16, 32, 64, 128];
box_sizes = box_sizes(box_sizes < p);
box_counts = zeros(size(box_sizes));

for i = 1:numel(box_sizes)
    s = box_sizes(i);
    % Reshape into blocks and check if any vessel pixel exists
    blocks_y = p / s;
    blocks_x = p / s;
    count = 0;
    for by = 1:blocks_y
        for bx = 1:blocks_x
            block = padded((by-1)*s + 1 : by*s, (bx-1)*s + 1 : bx*s);
            if any(block(:))
                count = count + 1;
            end
        end
    end
    box_counts(i) = count;
end

% Fit linear slope: log(N) = -D * log(s) + C => slope of log(N) vs log(1/s)
log_inv_s = log(1 ./ box_sizes);
log_n = log(box_counts);

coeffs = polyfit(log_inv_s, log_n, 1);
fd = coeffs(1);

% Ensure output is within physiological boundary (1.20 - 1.85)
fd = max(1.20, min(1.85, fd));

end
