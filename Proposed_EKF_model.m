clc
clear all
n=91;

z=xlsread('manas.xlsx','CT','A3:C450');
  
for t=1:4
CT(t,1)=z(1,3); %Intial core temperature considered constant for 4 minute
end

V(4)=0; %intial Varriance

for i=1:4
    HR(i,1)    = z(i,2);  %measured heart rate for intial 4 minute
end


HR_ma(1,1)=1;   %[false moving avarage
HR_ma(2,1)=2;
HR_ma(3,1)=3;
HR_ma(4,1)=4;        %for intial 4 minute]


% Coefficients for exercise measurment uapdate model (HR_model = -a1*CT^2+b1*CT-c1)
a1=4.5714;
b1=384.4286;
c1=7887.1;

% Coefficients for recovery measurment uapdate model (HR_model = -a2*CT^2+b2*CT-c2)
a2=4.5714;
b2=384.4286;
c2=7899.76;

gamma=0.022;
sigma=18.88;

for t=1:4
A(t,1)=40;  %A is a indicator to reperesent model switching. 
end         %A=40 represent exercise model, A=39 represent recovery model

for t=5:n

HR(t,1)    = z(t,2);   %Measured Heart rate
 
ct(t) = CT(t-1);

v(t) = V(t-1)+(gamma)^2;

HR_ma(t,1)= (HR(t-4)+HR(t-3)+HR(t-2)+HR(t-1)+HR(t))/5;

delta_HR(t,1)=HR_ma(t)-HR_ma(t-4);

if delta_HR(t,1)<0

    A(t,1)=39;
    
    c(t) = -2*a2*(ct(t)) + b2;

    k(t) = (v(t)*c(t))/((v(t)*(c(t))^2)+(sigma)^2);

    HR_model(t) = -a2*(ct(t))^2+b2*ct(t)-c2; % HR calculated by measurement model from primary pridicted CT.
    
    CT(t,1) = ct(t)+k(t)*(HR(t,1)-HR_model(t));
    
    
else
    
    A(t,1)=40;
    
    c(t) = -2*a1*(ct(t)) + b1;
 
    k(t) = (v(t)*c(t))/((v(t)*(c(t))^2)+(sigma)^2);

    HR_model(t) = -a1*(ct(t))^2+b1*ct(t)-c1; % HR calculated by measurement model from primary pridicted CT.
    
    CT(t,1) = ct(t)+k(t)*(HR(t,1)-HR_model(t));


end

V(t) = (1-k(t)*c(t))*v(t);

end