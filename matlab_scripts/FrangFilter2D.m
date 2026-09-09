function [outIm, What, Scale] = FrangiFilter2D(I, options)
% Frangi Filter for vessel enhancement
%
% Based on:
% A.F. Frangi et al., "Multiscale vessel enhancement filtering"
%
% Input:
%   I - Grayscale image
%   options - Structure with options
%     .FrangiScaleRange - [min, max] scales
%     .FrangiScaleRatio - Scale step ratio
%     .FrangiBetaOne - Beta one parameter
%     .FrangiBetaTwo - Beta two parameter
%
% Output:
%   outIm - Enhanced image
%   What - Hessian matrix
%   Scale - Scale used

% Default options
if nargin < 2
    options.FrangiScaleRange = [1, 4];
    options.FrangiScaleRatio = 0.5;
    options.FrangiBetaOne = 0.5;
    options.FrangiBetaTwo = 15;
end

% Convert to double
I = double(I);

% Normalize
I = I / max(I(:));

% Scale range
scale_range = options.FrangiScaleRange(1):options.FrangiScaleRatio:options.FrangiScaleRange(2);

% Initialize
outIm = zeros(size(I));
What = cell(length(scale_range), 1);
Scale = zeros(size(I));

for i = 1:length(scale_range)
    scale = scale_range(i);
    
    % Compute Hessian
    [Dxx, Dyy, Dxy] = Hessian2D(I, scale);
    
    % Eigenvalues
    [Lambda1, Lambda2] = eig2image(Dxx, Dxy, Dyy);
    
    % Vesselness
    Rb = (Lambda2 ./ Lambda1).^2;
    S2 = Lambda1.^2 + Lambda2.^2;
    
    % Vesselness measure
    V = (1 - exp(-2 * Rb / options.FrangiBetaOne^2)) .* ...
        (1 - exp(-2 * S2 / options.FrangiBetaTwo^2));
    
    % Update
    mask = V > outIm;
    outIm(mask) = V(mask);
    Scale(mask) = scale;
end

% Threshold
outIm = max(outIm, 0);
end

function [Dxx, Dyy, Dxy] = Hessian2D(I, sigma)
% Compute Hessian matrix
[x, y] = ndgrid(-round(3*sigma):round(3*sigma), -round(3*sigma):round(3*sigma));

% Gaussian kernel
G = exp(-(x.^2 + y.^2) / (2 * sigma^2));
G = G / sum(G(:));

% Derivatives
Gx = -x / sigma^2 .* G;
Gy = -y / sigma^2 .* G;
Gxx = (x.^2 / sigma^4 - 1/sigma^2) .* G;
Gyy = (y.^2 / sigma^4 - 1/sigma^2) .* G;
Gxy = (x .* y / sigma^4) .* G;

% Convolve
Dxx = imfilter(I, Gxx, 'symmetric', 'conv');
Dyy = imfilter(I, Gyy, 'symmetric', 'conv');
Dxy = imfilter(I, Gxy, 'symmetric', 'conv');
end

function [Lambda1, Lambda2] = eig2image(Dxx, Dxy, Dyy)
% Compute eigenvalues of Hessian
% Based on: 2x2 symmetric matrix
% |Dxx Dxy|
% |Dxy Dyy|

% Compute trace and determinant
trace = Dxx + Dyy;
det = Dxx .* Dyy - Dxy.^2;

% Compute eigenvalues
sqrt_disc = sqrt(max(trace.^2 - 4 * det, 0));
Lambda1 = (trace + sqrt_disc) / 2;
Lambda2 = (trace - sqrt_disc) / 2;

% Ensure proper order (Lambda1 > Lambda2)
mask = Lambda1 < Lambda2;
temp = Lambda1(mask);
Lambda1(mask) = Lambda2(mask);
Lambda2(mask) = temp;
end