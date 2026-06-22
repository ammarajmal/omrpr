%%==편중성분 제거
for i=1:nn
    dat0(:,i)=dat0(:,i)-Bias(1,i);
end

%%==변위보정(side sensor-center sensor)
dat0(:,1)=(dat0(:,1)+dat0(:,2))/2;
dat0(:,2)=(dat0(:,2)-dat0(:,1));

%%==voltage 값을 변위와 풍속으로 변환
for i=1:nn-1
    dat0(:,i)=dat0(:,i)*pvolt(i);
end

wind_vel_tunnel=4*sqrt(4.002*mean(dat0(:,nn)));

for i=1:nn-1
    wind_vel_1(:,i)=wind_vel_tunnel;
    wind_vel(:,i)=wind_vel_tunnel*ratio(:,i)*sqrt(scale);
end

%%==평균값계산

%==연직
mean_(:,1)=mean(dat0(:,1))*scale;  % cm 단위

%==비틀림(cm)
mean_(:,2)=mean(dat0(:,2))*scale*dp; % cm 단위

%==비틀림(deg)
%mean_(:,2)=asind((mean(dat0(:,2))*scale*dp)/((9.625*100)/2)); % deg 단위


%%==filtering
%fs = 360; fn = fs/2; dt = 1/fs;
       %f1 = 3.1260; band = 1.0; fl = f1-band; fh = f1+band; 
       %[b, a]=fir1(1000,[fl/fn fh/fn]); dat0(:,1) = filtfilt(b,a,dat0(:,1));

       %f1 = 10.0261; band = 1.0; fl = f1-band; fh = f1+band; 
       %[b, a]=fir1(1000,[fl/fn fh/fn]); dat0(:,2) = filtfilt(b,a,dat0(:,2));


%%==최대값 계산

%==연직
rms_(:,1)=std(dat0(:,1))*scale; % cm 단위
peak_(:,1)=max(abs(dat0(:,1)-mean((dat0(:,1)))))*scale; % cm 단위

%==비틀림(cm)
rms_(:,2)=std(dat0(:,2))*scale*dp; % cm 단위
peak_(:,2)=max(abs(dat0(:,2)-mean((dat0(:,2)))))*scale*dp; % cm 단위

%==비틀림(deg)
%rms_(:,2)=asind((std(dat0(:,2))*scale*dp)/((9.625*100)/2)); % deg 단위
%peak_(:,2)=asind((max(abs(dat0(:,2)-mean((dat0(:,2)))))*scale*dp)/((9.625*100)/2)); % deg 단위

%%==저장변수

AA=[wind_vel_1(1),wind_vel(1),mean_(1),rms_(1),peak_(1)];
BB=[wind_vel_1(2),wind_vel(2),mean_(2),rms_(2),peak_(2)];

result_bending=[result_bending;AA];
result_torsion=[result_torsion;BB];
