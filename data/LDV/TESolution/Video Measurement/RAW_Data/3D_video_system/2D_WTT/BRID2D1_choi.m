%===========Bridge Elastic Test 2 Dimensional(2 차원 주형 진동실험 데이타처리)
%===========2 자유도
%===========Ver. 2.0 2017.02.03, Programmed by kjm
%===========Ver. 2.1 2024.11.11, Modified by CHOI

clear; close all; clc;
disp('영상계측: 2차원 주형 진동실험')

%% Input
cn = 38;                 % 파일수

% calibration factor
scale = 1;              % 축소율
pvolt = [100, 100];     % [center,  side]

% location of sensor
dside = 10;             % side sensor 거리 [cm]
db = 20.0;              % 모형폭/2 or 비틀림변위 관찰위치 [cm]
dp = db/dside;          % 모형끝단에서의 비틀림 보정 환산

% natural frequency
fre_n=[1.000, 1.000];   % 요구치 [연직, 비틀림]
fre_e=[1.000, 1.000];   % 실험치 [연직, 비틀림]
ratio = fre_n./fre_e;

% output
result_bending=[];
result_torsion=[];


%% Load data
% Col 1 Time (s)
% Col 2 Cam1 Fiducial ID
% Col 3~9 Cam1 Position X,Y,Z Rotation X,Y,Z,W
% Col 10 Cam2 Fiducial ID
% Col 11~17 Cam2 Position X,Y,Z Rotation X,Y,Z,W
% Col 18 Cam3 Fiducial ID
% Col 19~25 Cam3 Position X,Y,Z Rotation X,Y,Z,W

for i = 0:cn-1
    filename = strcat('D',num2str(i));
    eval(strcat(filename,'_raw = xlsread(''',filename,'.csv'');'))
%   eval(strcat(filename,'_raw = load(''',filename,''');'))
    eval(strcat(filename,' = [',filename,'_raw(:,4), ',filename,'_raw(:,20)];'))    % Cam1 Y / Cam2 Y %%%%%%%%%%%%%%%%%%
end


%% Calculation
Bias = mean(D0);        % Bias

for j = 1:cn-1
    valname = strcat('D',num2str(j));
    eval(strcat('dat0 = ',valname,';'))    % dat0
    
    dat1 = (dat0 - Bias) .* pvolt;          % 편중성분 제거 & calibration factor
    dat2 = [ (dat1(:,1)+dat1(:,2))/2, (dat1(:,2)-dat1(:,1))/2 ];    % 변위보정(side sensor-center sensor)  %%%%%%%%%%%%%%%
    
    wind_vel_tunnel = 4*sqrt(4.346*mean(dat1));
    wind_vel = wind_vel_tunnel .* ratio * sqrt(scale);
    
    mean_dat = [ mean(dat2(:,1))*scale, mean(dat2(:,2))*scale*dp];    % mean
    rms_dat = [ std(dat2(:,1))*scale, std(dat2(:,2))*scale*dp];       % rms
    peak_dat = [ ( max(abs(dat2(:,1)))-mean_dat(1) )* scale, ...
        ( max(abs(dat2(:,2)))-mean_dat(2) )* scale * dp];             % peak
    
    AA=[wind_vel_tunnel(1),wind_vel(1),mean_dat(1),rms_dat(1),peak_dat(1)];
    BB=[wind_vel_tunnel(2),wind_vel(2),mean_dat(2),rms_dat(2),peak_dat(2)];
    
    result_bending=[result_bending;AA];
    result_torsion=[result_torsion;BB];
    
    clearvars dat0 dat1 dat2 wind_vel_tunnel wind_vel mean_dat rms_dat peak_dat AA BB
end

save result_bending.txt result_bending -ascii
save result_torsion.txt result_torsion -ascii

%=====================EOF