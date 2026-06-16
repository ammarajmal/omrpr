clc; clear all; close all;

% data1 : raw data
% data  : low pass filtered data
% data11: Free Vibration data

file = 'B1.csv'; 
nP = 80;                   % pn=number of peaks
idc= 3;                     % frequency & damping id channel
%cal1 = 34.303;                 
%cal2 = 32.684;
%cal2 = 32.684;
cal1 = 100;                 
cal2 = 100;
cal3 = 100;

fs = 48.70945; fn = fs/2; dt = 1/fs;
data1 = load(file);
data1 = [data1(:,1)*cal1,data1(:,2)*cal2,data1(:,3)*cal3];
data1 = detrend(data1,'constant'); data1 = detrend(data1);

BF_filter = 'wo'; % 'wi' of 'wo'
switch BF_filter
    case 'wo'
        cut = 10;
        [b,a] = butter(9,cut/fn); data = filtfilt(b,a,data1);
    case 'wi'
        f1 = 1.4; band = 0.01; fl = f1-band; fh = f1+band; 
        [b, a]=fir1(200,[fl/fn fh/fn]); data = filtfilt(b,a,data1);
end

% tor = [data(:,1)-data(:,4),data(:,2)-data(:,5),data(:,3)-data(:,6)];


nt = length(data); T = [0:dt:dt*(nt-1)]';

figure(1)
plot(data(:,:));grid;legend('Ch1','Ch2','Ch3')
% id1=2;subplot(212);plot(data(:,id1));grid;legend('Middle frame')
%puase

% 자유진동부분
index1 =1500;
zz1=index1:nt;

%%% MTMD1 자유진동 부분 추출
data11=data(zz1,:);
nn1=[length(zz1)];
T1 = [0:dt:dt*(nn1(1)-1)]';

figure(2)
subplot(211);plot(T1,data11(:,1));grid;legend('Ch1');xlabel('time(sec)');ylabel('Amplitude(mm)');%ylim([-200 200]);%title('Time History of band pass 8.0~8.2Hz');xlim([0 80]);
subplot(212);plot(T1,data11(:,2));grid;legend('Ch2');xlabel('time(sec)');ylabel('Amplitude(mm)');%ylim([-200 200]);%xlim([0 80])
subplot(313);plot(T1,data11(:,3));grid;legend('Ch3');xlabel('time(sec)');ylabel('Amplitude(mm)');%ylim([-200 200]);%xlim([0 80]);
% subplot(514);plot(T1,data11(:,4));grid;legend('Ch4');ylabel('Acc(cm/s^2)');ylim([-200 200]);%xlim([0 80]);
% subplot(515);plot(T1,data11(:,5));grid;legend('Ch5');xlabel('time(sec)');ylabel('Acc(cm/s^2)');ylim([-200 200]);%xlim([0 80]);

%% FFT with total data
Nf = 2^20; df = fn/(Nf/2); freq = 0:df:fn-df;

fdata = fft(data,Nf); 
amp   = abs(fdata(1:Nf/2,:))*dt; 

figure(3)
plot(freq,amp);grid;title('FFT with total data');
xlim([0 15]);xlabel('Frequency[Hz]');legend('Ch1','Ch2','Ch3');


fdata11 = fft(data11,Nf); 
amp11 = abs(fdata11(1:Nf/2,:))*dt; 

figure(4)
plot(freq,amp11);grid;title('FFT with FREE vibration data');
xlim([0 15]);xlabel('Frequency[Hz]');ylabel('Amplitude(mm)');legend('Ch1','Ch2','Ch3');


% ------ MTMD1 자유진동 분석 : 한계감쇠비 : 마찰계수
sprintf('Natural frequency based on the free vib.(TMD1):')
[vel1,i1]=max(amp11(:,idc)); 
TMD1_vel_freq1=freq(i1) 
nT1=[round(1/(TMD1_vel_freq1*dt))]; % nT=number of time steps for natural period

fvdata=data11(:,idc);          % fvdata = #1 TMD free vibration data
posPeak1=zeros(nP,1);
negPeak1=zeros(nP,1); 

for jj=1:nP
    temp=[fvdata((jj-1)*nT1+1:jj*nT1,1)];
    [vel_pos,time_posVel] = max(temp(:,1)); 
    [vel_neg,time_negVel] = min(temp(:,1)); 
    posPeak1(jj,:)=[vel_pos];
    negPeak1(jj,:)=[vel_neg];
    posTime1(jj,:)=[(time_posVel+((jj-1)*nT1+1))*dt];
    negTime1(jj,:)=[(time_negVel+((jj-1)*nT1+1))*dt];
end

aa=[1:nP]';

ppF1={polyfit(aa,log(posPeak1(:,1)),1)};
npF1={polyfit(aa,log(-negPeak1(:,1)),1)};

TMD1_posDamp=[(sqrt(ppF1{1,1}(1,1)^2/(ppF1{1,1}(1,1)^2+4*pi^2)))*2*pi]; 
TMD1_negDamp=[(sqrt(npF1{1,1}(1,1)^2/(npF1{1,1}(1,1)^2+4*pi^2)))*2*pi];  

sprintf('Damping ratio based on the free vib.:')
TMD1_vel_posDamp=TMD1_posDamp(1,1)
TMD1_vel_negDamp=TMD1_negDamp(1,1)
TMD1_vel_avgDamp=(TMD1_vel_posDamp+TMD1_vel_negDamp)/2

% figure(6)
% subplot(311);plot(T1,data11(:,idc),'b',posTime1(:,1),posPeak1(:,1),'go',negTime1(:,1),negPeak1(:,1),'gsquare');
% title('Vertical Acceleration of MTMD');ylabel('acc. (cm/s^2)');xlabel('Time (sec)');grid;xlim([0 50]);
% subplot(312);plot(aa,log(posPeak1(:,1)),'go',aa,(aa*ppF1{1,1}(1,1)+ppF1{1,1}(1,2)),'b--');
% title('Logarithmic Peak Value of Center Vel.');ylabel('Positive Peak');xlabel('Peak No.');grid;
% subplot(313);plot(aa,-log(-negPeak1(:,1)),'gsquare',aa,(aa*-npF1{1,1}(1,1)-npF1{1,1}(1,2)),'b--');
% ylabel('Negative Peak');xlabel('Peak No.');grid;

% 마찰계수
for nn=2:1:nP
    friction_pos(nn-1,:) = [(posPeak1(nn-1,1)-posPeak1(nn,1))/(4*981)];
    friction_neg(nn-1,:) = [(-negPeak1(nn-1,1)-(-negPeak1(nn,1)))/(4*981)];
end

%보고서 결과
result_freq = [TMD1_vel_freq1];
result_damp = [TMD1_vel_posDamp, TMD1_vel_negDamp, TMD1_vel_avgDamp];
result_friction = [mean(friction_pos(:,1)), mean(friction_neg(:,1)), (mean(friction_pos(:,1))+mean(friction_neg(:,1)))/2];
result_mtmd=[result_freq,result_damp]

figure(7)
subplot(211);plot(freq,amp11(:,1));grid;xlim([0 15]);xlabel('Frequency[Hz]');ylabel('Amplitude(mm)');title('FFT with FREE vibration data');legend('Ch1');
subplot(212);plot(freq,amp11(:,2));grid;xlim([0 15]);xlabel('Frequency[Hz]');ylabel('Amplitude(mm)');legend('Ch2');
%subplot(313);plot(freq,amp11(:,3));grid;xlim([0 5]);ylim([0 1400]);xlabel('Frequency[Hz]');ylabel('Amplitude');legend('Ch3');
% %subplot(514);plot(freq,amp11(:,4));grid;xlim([0 5]);ylim([0 1400]);ylabel('Amplitude');legend('Ch4');
% subplot(515);plot(freq,amp11(:,5));grid;xlim([0 5]);ylim([0 1400]);xlabel('Frequency[Hz]');ylabel('Amplitude');legend('Ch5');

result_fft=num2str(result_mtmd(:,1));
result_Pdamp=num2str(result_mtmd(:,2));
result_Ndamp=num2str(result_mtmd(:,3));
result_Adamp=num2str(result_mtmd(:,4));

scrsz = get(0,'ScreenSize');
figure('Position',[scrsz(3)/2.1 scrsz(4)/3 scrsz(3)/2 scrsz(4)/1.8])
subplot(311);set(gca,'Position',[0.1 0.75 0.85 0.2]);
plot(T1,data11(:,idc),'b',posTime1(:,1),posPeak1(:,1),'go',negTime1(:,1),negPeak1(:,1),'gsquare');
title('');ylabel('Amplitude(mm)');ylim([-2 2]);xlabel('Time (sec)');grid;xlim([0 60]);
subplot(312);set(gca,'Position',[0.1 0.42 0.85 0.2]);
plot(freq,amp11(:,idc));grid;title('FFT with Free vibration data');
xlim([0 15]);xlabel('Frequency[Hz]');ylabel('Amplitude(mm)');gtext([result_fft,'Hz']);
subplot(313);set(gca,'Position',[0.1 0.08 0.85 0.2]);
plot(aa,log(posPeak1(:,1)),'go',aa,(aa*ppF1{1,1}(1,1)+ppF1{1,1}(1,2)),'b--',aa,-log(-negPeak1(:,1)),'gsquare',aa,(aa*-npF1{1,1}(1,1)-npF1{1,1}(1,2)),'b--');
title('Logarithmic Peak Value');ylabel('Peak');xlabel('Peak No.');grid;ylim([-2 2]);set(gca,'ytick',[-6:1:6]);
text(2.5,-1,['Negative Damping ratio : ',result_Ndamp,]);
text(2.5,1,['Positive Damping ratio : ',result_Pdamp,]);
text(1.05,0.0,['Average Damping ratio : ',result_Adamp,]);
