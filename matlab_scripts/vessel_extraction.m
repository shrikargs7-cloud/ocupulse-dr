function [vessel_mask, skeleton, metrics] = vessel_extraction(img)
% VESSEL_EXTRACTION Segments retinal vessels, centerlines, and geometry
%
% Inputs:
%   img - RGB retinal fundus photograph
%
% Outputs:
%   vessel_mask - Binary vessel segmentation (1 = vessel, 0 = background)
%   skeleton    - 1-pixel centerline vascular tree
%   metrics     - Structure with density, length, branch points, tortuosity

if size(img, 3) == 3
    % Peak contrast of hemoglobin is in the green spectral band
    green = img(:, :, 2);
else
    green = img;
end

% 1. Complement green channel so vessels are bright ridges
inv_green = imcomplement(green);

% 2. Adaptive CLAHE contrast enhancement
enhanced = adapthisteq(inv_green, 'ClipLimit', 0.03, 'Distribution', 'rayleigh');

% 3. Multi-scale Top-Hat morphological filtering
se1 = strel('disk', 3);
se2 = strel('disk', 7);
tophat1 = imtophat(enhanced, se1);
tophat2 = imtophat(enhanced, se2);
multiscale = 0.6 * double(tophat1) + 0.4 * double(tophat2);
multiscale = uint8(255 * (multiscale / max(multiscale(:))));

% 4. Adaptive thresholding within Retinal ROI
roi_mask = green > 15;
threshold = graythresh(multiscale(roi_mask)) * 0.9;
raw_vessels = imbinarize(multiscale, threshold) & roi_mask;

% 5. Area open to suppress isolated speckle noise (< 20 pixels)
vessel_mask = bwareaopen(raw_vessels, 20);

% 6. Morphological thinning to 1-pixel centerline skeleton
skeleton = bwmorph(vessel_mask, 'thin', Inf);

% 7. Quantitative Biomarkers
vessel_area = sum(vessel_mask(:));
roi_area = sum(roi_mask(:));
vessel_density = (vessel_area / max(1, roi_area)) * 100.0;
vessel_length = sum(skeleton(:));

% Junctions and branch points (endpoints & branchpoints)
branch_points = bwmorph(skeleton, 'branchpoints');
endpoints = bwmorph(skeleton, 'endpoints');

metrics = struct();
metrics.vessel_density = vessel_density;
metrics.vessel_area = vessel_area;
metrics.vessel_length_pixels = vessel_length;
metrics.branch_points = sum(branch_points(:));
metrics.endpoints = sum(endpoints(:));
metrics.average_width = vessel_area / max(1, vessel_length);

end
