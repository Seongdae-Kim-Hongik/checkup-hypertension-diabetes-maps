#  주모형(S1_narrative_full + 강제 5, NB BYM2+RW1+iid, 593 그래프) 기준으로:
#   P0 주모형 재적합(기준) · P1 +이미 진단된 비율(검진 유질환자 고혈압·당뇨 ÷ 수검자; 진단 경쟁 가설) · P2 역방향 변수 단독(+강제) ·
#   P3 같은 축 변수 제외(혈당 인지율 ↔ 혈압 인지율, 비만 ↔ 걷기·중강도, 수급률 ↔ 대졸·1인가구) · P4 지역 간·지역 내 분해(역방향 3 + 대졸·혈압 인지율)
#  사용(01_스크립트/): TAG=UNDX ST_VER=std3 ST_GRAPH=<graph_593> ./rslot.sh Rscript 88U_undx_reverse_posthoc.R  → results_std3/S46_undx_posthoc.csv
suppressPackageStartupMessages({library(INLA);library(sf);library(jsonlite)})
TAG<-Sys.getenv("TAG","UNDX");VER<-Sys.getenv("ST_VER","std3");inla.setOption(num.threads="1:1")
OUTD<-file.path("..","04_분석",TAG);RES<-file.path(OUTD,paste0("results_",VER))
SHP<-Sys.getenv("ST_SHP",file.path(normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),"..")),"data","boundary","final.shp"))
S<-fromJSON(file.path(OUTD,sprintf("config_%s_%s.json",TAG,VER)),simplifyVector=TRUE)
DD<-read.csv(file.path(OUTD,sprintf("panel_%s_%s.csv",TAG,VER)),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);DD$fbd_region<-enc2utf8(DD$fbd_region)
G<-st_read(SHP,quiet=TRUE);G$region<-enc2utf8(G$region);g<-inla.read.graph(Sys.getenv("ST_GRAPH"));stopifnot(g$n==nrow(G))
DD$area<-match(DD$fbd_region,G$region);DD$time<-DD$year-min(DD$year)+1;DD$yiid<-DD$time
FORCED<-S$forced;HYP<-as.character(S$sets_after_vif$S1_narrative_full)
pc<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)),phi=list(prior="pc",param=c(0.5,2/3)));pcp<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)))
REV<-c("glucose_awareness_rate","obesity_rate","basic_livelihood_rate");EXTRA<-c("tertiary_educated_share","bp_awareness_rate")
# 지역 간(시군구 평균, 재표준화)·지역 내(연도 편차) 성분
for(v in c(REV,EXTRA)){m<-ave(DD[[v]],DD$fbd_region);DD[[paste0(v,"__B")]]<-(m-mean(m))/sd(m);w<-DD[[v]]-m;DD[[paste0(v,"__W")]]<-w/sd(w)}
fit<-function(vars){f<-as.formula(paste("cases ~ 1 +",paste(sprintf("`%s`",vars),collapse="+"),"+ f(area,model='bym2',graph=g,scale.model=TRUE,constr=TRUE,hyper=pc) + f(time,model='rw1',scale.model=TRUE,hyper=pcp) + f(yiid,model='iid',hyper=pcp)"))
  inla(f,family="nbinomial",data=DD,E=DD$E,control.fixed=list(mean=0,prec=4,mean.intercept=0,prec.intercept=0.001),control.compute=list(waic=TRUE),control.inla=list(control.vb=list(emergency=50)))}
out<-NULL
add<-function(an,m,vs){fx<-m$summary.fixed;for(v in vs){if(!v%in%rownames(fx))next;r<-fx[v,];out<<-rbind(out,data.frame(analysis=an,cov=v,IRR=round(exp(r$mean),4),lo=round(exp(r$`0.025quant`),4),hi=round(exp(r$`0.975quant`),4),cred=(exp(r$`0.025quant`)>1|exp(r$`0.975quant`)<1),WAIC=round(m$waic$waic,1)))};cat(an,"done\n")}
MAIN<-unique(c(HYP,FORCED))
add("P0_main",fit(MAIN),c(REV,EXTRA))
add("P1_plus_diagnosed_share",fit(c(MAIN,"ext__dx_htn_share","ext__dx_dm_share")),c(REV,EXTRA,"ext__dx_htn_share","ext__dx_dm_share"))
for(v in REV)add(paste0("P2_alone_",v),fit(c(v,FORCED)),v)
AX<-list(glucose_awareness_rate="bp_awareness_rate",obesity_rate=c("walking_practice_rate","moderate_pa_rate"),basic_livelihood_rate=c("tertiary_educated_share","single_person_household_share"))
for(v in REV)add(paste0("P3_drop_axis_",v),fit(setdiff(MAIN,AX[[v]])),v)
DEC<-c(REV,EXTRA);vv<-c(setdiff(MAIN,DEC),paste0(DEC,"__B"),paste0(DEC,"__W"))
add("P4_between_within",fit(vv),c(paste0(DEC,"__B"),paste0(DEC,"__W")))
write.csv(out,file.path(RES,"S46_undx_posthoc.csv"),row.names=FALSE);print(out)
