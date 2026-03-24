import React from 'react';

const LoginPage = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        {/* Logo sau Titlu */}
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-800">MIEZ</h2>
          <p className="text-gray-500 mt-2">Bine ai revenit! Te rugăm să te autentifici.</p>
        </div>

        <form className="space-y-6">
          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input 
              type="email" 
              className="mt-1 block w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
              placeholder="nume@exemplu.com"
            />
          </div>

          {/* Parola */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Parolă</label>
            <input 
              type="password" 
              className="mt-1 block w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
              placeholder="••••••••"
            />
          </div>

          {/* Remember me & Forgot Password */}
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input type="checkbox" className="h-4 w-4 text-blue-600 border-gray-300 rounded" />
              <label className="ml-2 block text-sm text-gray-700">Ține-mă minte</label>
            </div>
            <a href="#" className="text-sm text-blue-600 hover:underline">Ai uitat parola?</a>
          </div>

          {/* Buton Login */}
          <button 
            type="submit" 
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            Intră în cont
          </button>
        </form>

        {/* Footer Login */}
        <div className="mt-8 text-center text-sm text-gray-600">
          Nu ai un cont? <a href="#" className="text-blue-600 font-medium hover:underline">Înregistrează-te</a>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;