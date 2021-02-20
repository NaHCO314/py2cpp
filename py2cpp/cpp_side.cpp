#include<bits/stdc++.h>
template <typename T>bool py_is(const std::vector<T>&a,const std::vector<T>&b){return&a==&b;}
template <typename T>bool py_is(T a, T b){return a==b;}
template <typename T, typename U>bool py_is(T a, U b){return false;}
template <typename T>bool py_in(const std::vector<T>&a,T b){return std::find(a.begin(), a.end(), b) != a.end();}
template <typename T, typename U>bool py_in(const std::vector<T>&a,U b){return false;}

auto py_mod(auto n, auto m){
  return ((n < 0) ^ (m < 0))? m + fmod(n, m) : fmod(n, m);
}

int main(){



}
