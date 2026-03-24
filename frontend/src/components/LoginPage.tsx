import React, { useState } from 'react';

const UserIcon = () => (
  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
);

const LockIcon = () => (
  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
  </svg>
);

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Login attempt:", { username, password });
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-b from-[#1a1a1a] via-[#1a1a1a] to-[#4a1a1a]">
      {/* Containerul principal este acum max-w-sm (mai îngust) */}
      <div className="max-w-sm w-full flex flex-col items-center">
        
        {/* LOGO SECTION - Micșorat distanțele */}
        <div className="flex flex-col items-center mb-8">
          <div className="bg-[#cc333a] rounded-xl p-3 mb-3 shadow-lg">
            <span className="text-white text-3xl font-black leading-none">M</span>
          </div>
          <h1 className="text-white text-2xl font-bold tracking-[0.2em]">M.I.E.Z</h1>
          <p className="text-white/50 mt-1 text-xs font-light">Enterprise Resource Planning</p>
        </div>

        {/* MAIN CARD - Padding redus la p-8 și rotunjire ajustată */}
        <div className="bg-white rounded-[2rem] shadow-2xl p-8 w-full mb-8">
          <h2 className="text-gray-800 text-2xl font-bold text-center mb-8">Sign In</h2>

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-xs font-bold text-gray-500 mb-1.5 ml-1">Username</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <UserIcon />
                </span>
                <input
                  type="text"
                  placeholder="Enter username"
                  className="w-full pl-12 pr-4 py-3 bg-white border border-gray-100 rounded-full focus:ring-2 focus:ring-[#cc333a]/20 focus:border-[#cc333a] outline-none transition-all text-sm placeholder:text-gray-300"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-500 mb-1.5 ml-1">Password</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <LockIcon />
                </span>
                <input
                  type="password"
                  placeholder="Enter password"
                  className="w-full pl-12 pr-4 py-3 bg-white border border-gray-100 rounded-full focus:ring-2 focus:ring-[#cc333a]/20 focus:border-[#cc333a] outline-none transition-all text-sm placeholder:text-gray-300"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-3.5 bg-[#cc333a] hover:bg-[#b02a30] text-white font-bold rounded-full transition-colors shadow-lg shadow-[#cc333a]/20 mt-2 text-sm"
            >
              Sign In
            </button>
          </form>

          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-gray-50"></span></div>
          </div>

          {/* DEMO CREDENTIALS - Mai compact */}
          <div className="text-center">
            <p className="text-gray-400 text-[10px] font-medium mb-3 uppercase tracking-wider">Demo Credentials</p>
            <div className="bg-[#fcfcfc] border border-gray-50 rounded-xl p-4 space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">Username:</span>
                <span className="text-gray-700 font-bold">user</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">Password:</span>
                <span className="text-gray-700 font-bold">password</span>
              </div>
            </div>
          </div>
        </div>

        {/* FOOTER */}
        <p className="text-white/30 text-[9px] tracking-[0.3em] uppercase">
          © 2026 M.I.E.Z. All rights reserved.
        </p>
      </div>
    </div>
  );
};

export default LoginPage;