/* Portable C99 implementation of the same numeric loops as equity_engine.py.
 * Build: cc -O3 -std=c99 -fPIC -shared -march=x86-64 -mtune=generic
 *           native/plo5_fast.c -o native/plo5_fast_linux_x86_64.so
 * No hidden state: tables are read-only, and the RNG state is an argument.
 */
#include <stdint.h>
#include <stddef.h>

static const int32_t *ranks;
static const int64_t *keys;
static const float *equities;
static int nkeys;
static const int32_t powers[9] = {1,5,25,125,625,3125,15625,78125,390625};

void fast_init(const int32_t *t, const int64_t *k, const float *e, int n) {
    ranks=t; keys=k; equities=e; nkeys=n;
}

int32_t fast_five(int a,int b,int c,int d,int e) {
    int32_t v=ranks[powers[a>>2]+powers[b>>2]+powers[c>>2]+powers[d>>2]+powers[e>>2]];
    if ((a&3)==(b&3) && (a&3)==(c&3) && (a&3)==(d&3) && (a&3)==(e&3))
        v += ((v>>20)==3 ? 5 : 6)<<20;
    return v;
}

int32_t fast_score(const int32_t *h,const int32_t *b,int n) {
    int32_t best=0;
    for(int i=0;i<4;i++) for(int j=i+1;j<5;j++)
        for(int a=0;a<n-2;a++) for(int c=a+1;c<n-1;c++) for(int d=c+1;d<n;d++) {
            int32_t v=fast_five(h[i],h[j],b[a],b[c],b[d]);
            if(v>best)best=v;
        }
    return best;
}

double fast_equity(const int32_t *h) {
    int64_t m[4]={0,0,0,0};
    for(int i=0;i<5;i++) m[h[i]&3] |= (int64_t)1<<(h[i]>>2);
    for(int i=1;i<4;i++) for(int j=i;j>0 && m[j]<m[j-1];j--) {
        int64_t v=m[j];m[j]=m[j-1];m[j-1]=v;
    }
    int64_t key=m[0]|(m[1]<<9)|(m[2]<<18)|(m[3]<<27);
    int lo=0,hi=nkeys;
    while(lo<hi) {
        int mid=(lo+hi)/2;
        if(keys[mid]<key)lo=mid+1;else hi=mid;
    }
    return lo<nkeys && keys[lo]==key ? equities[lo] : -1.0;
}

static uint64_t random_next(uint64_t *s) {
    *s ^= *s>>12; *s ^= *s<<25; *s ^= *s>>27;
    return *s * UINT64_C(2685821657736338717);
}

static void make_grid(const int32_t *b,int n,int32_t *g) {
    uint64_t occupied=0;
    for(int i=0;i<n;i++) occupied |= UINT64_C(1)<<b[i];
    for(int i=0;i<1296;i++)g[i]=0;
    for(int i=0;i<35;i++)if(!(occupied&(UINT64_C(1)<<i)))
        for(int j=i+1;j<36;j++)if(!(occupied&(UINT64_C(1)<<j))) {
            int best=0;
            for(int a=0;a<n-2;a++)for(int c=a+1;c<n-1;c++)for(int d=c+1;d<n;d++) {
                int v=fast_five(i,j,b[a],b[c],b[d]);if(v>best)best=v;
            }
            g[i*36+j]=g[j*36+i]=best;
        }
}

static int grid_score(const int32_t *h,const int32_t *g) {
    int best=0;
    for(int i=0;i<4;i++)for(int j=i+1;j<5;j++) {
        int v=g[h[i]*36+h[j]];if(v>best)best=v;
    }
    return best;
}

uint64_t fast_simulate(const int32_t *h,const int32_t *b,int nb,int count,
        uint64_t state,int32_t *hands,double *values,double *outcomes,double *future) {
    uint64_t occupied=0;
    for(int i=0;i<5;i++)occupied|=UINT64_C(1)<<h[i];
    for(int i=0;i<nb;i++)occupied|=UINT64_C(1)<<b[i];
    int32_t deck[36],full[5],idxs[10],draw[10],grids[3][1296];
    int n=0;
    for(int i=0;i<36;i++)if(!(occupied&(UINT64_C(1)<<i)))deck[n++]=i;
    for(int i=0;i<nb;i++)full[i]=b[i];
    int fixed=0;
    if(nb==5) {
        for(int s=0;s<3;s++)make_grid(b,s+3,grids[s]);
        fixed=grid_score(h,grids[2]);
    }
    for(int row=0;row<count;row++) {
        int needed=10-nb;
        for(int j=0;j<needed;j++) {
            int k=j+(int)(random_next(&state)%(uint64_t)(n-j));idxs[j]=k;
            int32_t t=deck[j];deck[j]=deck[k];deck[k]=t;draw[j]=deck[j];
        }
        int32_t *opp=hands+5*row;
        double *v=values+4*row;
        for(int j=0;j<5;j++)opp[j]=draw[j];
        v[0]=fast_equity(opp);v[1]=v[2]=v[3]=0;
        int mine,theirs;
        if(nb==5) {
            for(int s=0;s<3;s++)v[s+1]=grid_score(opp,grids[s]);
            mine=fixed;theirs=(int)v[3];
        } else {
            if(nb>=3)v[1]=fast_score(opp,b,3);
            if(nb>=4)v[2]=fast_score(opp,b,4);
            for(int j=nb;j<5;j++)full[j]=draw[5+j-nb];
            mine=fast_score(h,full,5);theirs=fast_score(opp,full,5);
        }
        outcomes[row]=mine>theirs ? 1.0 : (mine==theirs ? 0.5 : 0.0);
        future[row]=theirs;
        for(int j=needed-1;j>=0;j--) {
            int k=idxs[j];int32_t t=deck[j];deck[j]=deck[k];deck[k]=t;
        }
    }
    return state;
}
