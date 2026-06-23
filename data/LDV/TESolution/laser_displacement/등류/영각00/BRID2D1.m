%%=====BET2D.m
%%=====Bridge Elastic Test 2 Dimensional(2 차원 주형 진동실험 데이타처리)
%===========2 자유도
%===========Ver. 2.0_2017.02.03, Programmed by kjm

clear all

%=======================================
%    Input 
%=======================================

sprintf('영상계측')

%%축소율
scale=1;
%%calibration
pvolt=[2.7, 2.7];      % [center,  side]
%% side sensor 거리
dside=13           % cm
%% 모형폭/2 or 비틀림변위 관찰위치
db=20      % cm
%% 모형끝단에서의 비틀림 보정 환산
dp=db/dside;
%%natural frequency
fre_n=[1, 1];   % 요구치 [연직, 비틀림]
fre_e=[1, 1];   % 실험치 [연직, 비틀림]

jj=size(fre_n,2);

ratio=zeros(1,jj);
for i=1:jj
    ratio(i)=fre_n(i)/fre_e(i);
end

%============================== end of input

result_bending=[];
result_torsion=[];

%% data 구성
%---DXX=[연직, 비틀림, 풍속]

%%편중성분
load D00
Bias=mean(D00);
nn=size(Bias,2);



load D01;  dat0=D01;  clear D01
n=1;
brid2d_sub1

load D02;  dat0=D02;  clear D02
n=2;
brid2d_sub1

load D03;  dat0=D03;  clear D03
n=3;
brid2d_sub1

load D04;  dat0=D04;  clear D04
n=4;
brid2d_sub1

load D05;  dat0=D05;  clear D05
n=5;
brid2d_sub1

load D06;  dat0=D06;  clear D06
n=6;
brid2d_sub1

load D07;  dat0=D07;  clear D07
n=7;
brid2d_sub1

load D08;  dat0=D08;  clear D08
n=8;
brid2d_sub1

load D09;  dat0=D09;  clear D09
n=9;
brid2d_sub1

load D10;  dat0=D10;  clear D10
n=10;
brid2d_sub1

load D11;  dat0=D11;  clear D11
n=11;
brid2d_sub1

load D12;  dat0=D12;  clear D12
n=12;
brid2d_sub1

load D13;  dat0=D13;  clear D13
n=13;
brid2d_sub1

load D14;  dat0=D14;  clear D14
n=14;
brid2d_sub1

load D15;  dat0=D15;  clear D15
n=15;
brid2d_sub1

load D16;  dat0=D16;  clear D16
n=16;
brid2d_sub1

load D17;  dat0=D17;  clear D17
n=17;
brid2d_sub1

load D18;  dat0=D18;  clear D18
n=18;
brid2d_sub1

load D19;  dat0=D19;  clear D19
n=19;
brid2d_sub1

load D20;  dat0=D20;  clear D20
n=20;
brid2d_sub1



save result_bending.txt result_bending -ascii
save result_torsion.txt result_torsion -ascii
clear all


%=====================EOF
