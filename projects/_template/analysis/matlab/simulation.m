projectRoot = fileparts(fileparts(fileparts(mfilename('fullpath'))));
figuresDir = fullfile(projectRoot, 'figures', 'final');
if ~exist(figuresDir, 'dir')
    mkdir(figuresDir);
end

disp(['Project root: ', projectRoot]);
disp('Replace this template with project-specific MATLAB simulation.');

