function visualize_uav(pos, orient)
% visualize_uav(pos, orient)
%   pos    = [x y z]
%   orient = [roll pitch yaw]
%
%   Displays a 4-panel UAV visualization window.

persistent fig traj_ax alt_ax orient_ax anim_ax ...
           pos_hist t_hist t0 uav_scene uav_platform

% --- One-time setup ---
if isempty(fig) || ~isvalid(fig)
    disp('Initializing UAV 4-window visualization...');

    fig = figure('Name','UAV 4-Window Display',...
                 'NumberTitle','off',...
                 'Color','w',...
                 'Position',[100 100 1200 700]);
    tl = tiledlayout(fig,2,2,'Padding','compact','TileSpacing','compact');

    % 1️⃣ XY trajectory
    traj_ax = nexttile(tl,1);
    hold(traj_ax,'on'); grid(traj_ax,'on');
    xlabel(traj_ax,'X [m]'); ylabel(traj_ax,'Y [m]');
    title(traj_ax,'XY Position Trace');

    % 2️⃣ Altitude vs Time
    alt_ax = nexttile(tl,2);
    hold(alt_ax,'on'); grid(alt_ax,'on');
    xlabel(alt_ax,'Time [s]'); ylabel(alt_ax,'Altitude [m]');
    title(alt_ax,'Altitude vs Time');

    % 3️⃣ Orientation Frame
    orient_ax = nexttile(tl,3);
    hold(orient_ax,'on'); grid(orient_ax,'on'); axis(orient_ax,'equal');
    xlabel(orient_ax,'X'); ylabel(orient_ax,'Y'); zlabel(orient_ax,'Z');
    title(orient_ax,'Orientation Frame');
    view(orient_ax,3);
    plotFrame(orient_ax, eye(3), [0 0 0], 'Fixed');

    % 4️⃣ UAV 3-D Animation
    anim_ax = nexttile(tl,4);
    hold(anim_ax,'on'); grid(anim_ax,'on');
    xlabel(anim_ax,'X [m]'); ylabel(anim_ax,'Y [m]'); zlabel(anim_ax,'Z [m]');
    title(anim_ax,'UAV Animation');
    view(anim_ax,3); axis(anim_ax,[-5 5 -5 5 0 5]);

    % Create UAV mesh
    uav_scene = uavScenario("UpdateRate",20,"StopTime",100);
    uav_platform = uavPlatform("UAV", uav_scene, ...
        "Trajectory", waypointTrajectory, ...
        "Mesh", uavMesh("quadrotor","Scale",0.6));
    show3D(uav_scene,'Parent',anim_ax);

    % Initialize data
    pos_hist = [];  t_hist = [];  t0 = tic;
end

% --- Update plots ---
t = toc(t0);
pos_hist = [pos_hist; pos];
t_hist   = [t_hist; t];
if size(pos_hist,1) > 500
    pos_hist = pos_hist(end-500:end,:);
    t_hist   = t_hist(end-500:end);
end

% 1️⃣ XY
cla(traj_ax);
plot(traj_ax,pos_hist(:,1),pos_hist(:,2),'b');
plot(traj_ax,pos(1),pos(2),'ro');

% 2️⃣ Altitude
cla(alt_ax);
plot(alt_ax,t_hist,pos_hist(:,3),'r');

% 3️⃣ Orientation
cla(orient_ax);
R = eul2rotm(orient,'ZYX');
plotFrame(orient_ax,eye(3),[0 0 0],'Fixed');
plotFrame(orient_ax,R,[0 0 0],'Body');

% 4️⃣ UAV animation
if ~isempty(uav_platform)
    movePlatform(uav_platform,pos,orient);
    show3D(uav_scene,'Parent',anim_ax,'FastUpdate',true);
end

drawnow limitrate

end

% === Helper ===
function plotFrame(ax,R,origin,label)
quiver3(ax,origin(1),origin(2),origin(3),R(1,1),R(2,1),R(3,1),0.5,'r','LineWidth',1.5);
quiver3(ax,origin(1),origin(2),origin(3),R(1,2),R(2,2),R(3,2),0.5,'g','LineWidth',1.5);
quiver3(ax,origin(1),origin(2),origin(3),R(1,3),R(2,3),R(3,3),0.5,'b','LineWidth',1.5);
text(ax,origin(1),origin(2),origin(3),label,'FontSize',10,'Color','k');
end
