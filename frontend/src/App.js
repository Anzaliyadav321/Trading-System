import React, { useState, useEffect } from 'react';

// ============================================
// AUTH CONTEXT & PROVIDER
// ============================================

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const AuthContext = React.createContext(null);
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true); // ⬅️ CHANGE 1: Change from false to true

  // ⬅️ CHANGE 2: Add this NEW useEffect to load token from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
    } else {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token); // ⬅️ CHANGE 3: Add this line to save token
      
      fetch(`${API_BASE_URL}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.json())
        .then(data => {
          if (data.email) {
            setUser(data);
          } else {
            setToken(null);
            localStorage.removeItem('token'); // ⬅️ CHANGE 4: Add this line
          }
        })
        .catch(() => {
          setToken(null);
          localStorage.removeItem('token'); // ⬅️ CHANGE 5: Add this line
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    formData.append('grant_type', 'password');
    
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: formData
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }

    setToken(data.access_token);
    return data;
  };

  const register = async (email, password) => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Registration failed');
    }

    return data;
  };

  const verifyOTP = async (email, otp) => {
    const response = await fetch(`${API_BASE_URL}/auth/verify-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp })
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'OTP verification failed');
    }

    return data;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token'); // ⬅️ CHANGE 6: Add this line
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, verifyOTP, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// ============================================
// API SERVICE
// ============================================

const apiService = {
  async getTodaySignals(token) {
    const response = await fetch(`${API_BASE_URL}/signals/today`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Failed to fetch signals');
    return response.json();
  },

  async refreshSignals(token) {
    const response = await fetch(`${API_BASE_URL}/signals/refresh`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Failed to refresh signals');
    return response.json();
  },

  async bookOrder(token, orderData) {
    const response = await fetch(`${API_BASE_URL}/orders/book-order`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(orderData)
    });
    if (!response.ok) throw new Error('Failed to book order');
    return response.json();
  },

  async getOrderHistory(token, symbol) {
    const response = await fetch(`${API_BASE_URL}/orders/history/${symbol}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Failed to fetch order history');
    return response.json();
  },

  async getAllOrderHistory(token) {
    const response = await fetch(`${API_BASE_URL}/orders/all-history`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Failed to fetch all order history');
    return response.json();
  }
};

// ============================================
// LOGIN FORM
// ============================================

const LoginForm = ({ onSwitchToRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async () => {
    setError('');
    setLoading(true);

    try {
      await login(email, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md">
      <div className="bg-white rounded-2xl shadow-2xl p-8 border border-gray-200">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">📈</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-800 mb-2">Trading System</h2>
          <p className="text-gray-600">Sign in to your account</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
            <p className="text-sm text-red-800 font-medium">{error}</p>
          </div>
        )}

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
              className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="your@email.com"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
              className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="••••••••"
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading}
            className={`w-full py-3 rounded-xl text-white font-semibold transition-all shadow-lg ${
              loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700'
            }`}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </div>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Don't have an account?{' '}
            <button onClick={onSwitchToRegister} className="text-blue-600 hover:text-blue-700 font-semibold">
              Sign up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// ============================================
// OTP VERIFICATION FORM
// ============================================

const OTPVerificationForm = ({ email, onSwitchToLogin, onVerified }) => {
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const { verifyOTP } = useAuth();

  const handleSubmit = async () => {
    setError('');
    setSuccess('');

    if (otp.length !== 6) {
      setError('OTP must be 6 digits');
      return;
    }

    setLoading(true);

    try {
      const result = await verifyOTP(email, otp);
      setSuccess(result.message || 'Email verified successfully!');
      setTimeout(() => onVerified(), 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md">
      <div className="bg-white rounded-2xl shadow-2xl p-8 border border-gray-200">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl"></span>
          </div>
          <h2 className="text-3xl font-bold text-gray-800 mb-2">Verify Email</h2>
          <p className="text-gray-600">Enter the OTP sent to</p>
          <p className="text-blue-600 font-semibold text-sm mt-1">{email}</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
            <p className="text-sm text-red-800 font-medium">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl">
            <p className="text-sm text-green-800 font-medium">{success}</p>
          </div>
        )}

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Enter 6-Digit OTP</label>
            <input
              type="text"
              maxLength="6"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
              className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-2xl text-center font-mono tracking-widest focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="000000"
              disabled={loading || success}
            />
            <p className="text-xs text-gray-500 mt-2 text-center">
              Check your email inbox (and spam folder)
            </p>
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading || success || otp.length !== 6}
            className={`w-full py-3 rounded-xl text-white font-semibold transition-all shadow-lg ${
              loading || success || otp.length !== 6
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700'
            }`}
          >
            {loading ? 'Verifying...' : success ? 'Verified!' : 'Verify OTP'}
          </button>
        </div>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Already verified?{' '}
            <button onClick={onSwitchToLogin} className="text-purple-600 hover:text-purple-700 font-semibold">
              Back to login
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// ============================================
// REGISTER FORM
// ============================================


const RegisterForm = ({ onSwitchToLogin, onRegistrationSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  const handleSubmit = async () => {
    setError('');
    setSuccess('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    try {
      const result = await register(email, password);
      setSuccess(result.message || 'Registration successful! Check your email for OTP.');
      setTimeout(() => onRegistrationSuccess(email), 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md">
      <div className="bg-white rounded-2xl shadow-2xl p-8 border border-gray-200">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl"></span>
          </div>
          <h2 className="text-3xl font-bold text-gray-800 mb-2">Create Account</h2>
          <p className="text-gray-600">Join the trading platform</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
            <p className="text-sm text-red-800 font-medium">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl">
            <p className="text-sm text-green-800 font-medium">{success}</p>
          </div>
        )}

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="your@email.com"
              disabled={loading || success}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="••••••••"
              disabled={loading || success}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
              className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="••••••••"
              disabled={loading || success}
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading || success}
            className={`w-full py-3 rounded-xl text-white font-semibold transition-all shadow-lg ${
              loading || success ? 'bg-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700'
            }`}
          >
            {loading ? 'Creating...' : success ? 'Success!' : 'Create Account'}
          </button>
        </div>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Already have an account?{' '}
            <button onClick={onSwitchToLogin} className="text-green-600 hover:text-green-700 font-semibold">
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// ============================================
// AUTH WRAPPER
// ============================================

const AuthWrapper = ({ children }) => {
  const { token, loading, logout, user } = useAuth();
  const [showForm, setShowForm] = useState('login');
  const [registeredEmail, setRegisteredEmail] = useState('');

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
            <span className="text-3xl">⏳</span>
          </div>
          <p className="text-gray-600 font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
        {showForm === 'login' && (
          <LoginForm onSwitchToRegister={() => setShowForm('register')} />
        )}
        {showForm === 'register' && (
          <RegisterForm 
            onSwitchToLogin={() => setShowForm('login')} 
            onRegistrationSuccess={(email) => {
              setRegisteredEmail(email);
              setShowForm('verify-otp');
            }}
          />
        )}
        {showForm === 'verify-otp' && (
          <OTPVerificationForm 
            email={registeredEmail}
            onSwitchToLogin={() => setShowForm('login')}
            onVerified={() => setShowForm('login')}
          />
        )}
      </div>
    );
  }

  return (
    <div className="relative">
      <div className="fixed top-4 right-4 z-[9999] flex items-center space-x-3 bg-white/95 backdrop-blur-sm rounded-xl p-2 shadow-lg border border-gray-200">
        <div className="px-3 py-1 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg">
          <p className="text-xs text-gray-700 font-medium">{user?.email}</p>
        </div>
        <button
          onClick={logout}
          className="px-4 py-2 bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 text-white rounded-lg font-semibold transition-all text-sm shadow-sm"
        >
          Logout
        </button>
      </div>
      {children}
    </div>
  );
};

// ============================================
// SIMPLIFIED TRADING DASHboard
// ============================================

// Book Sell Popup Component with Stop-Loss Position Tracking
const BookSellPopup = ({ signal, isOpen, onClose, onConfirm, token }) => {
  const [quantity, setQuantity] = useState(0);
  const [price, setPrice] = useState(signal?.clPrice || 0);
  const [amount, setAmount] = useState(0);
  const [validationError, setValidationError] = useState('');
  const [loading, setLoading] = useState(false);
  const [slPosition, setSlPosition] = useState(null);
  
  const previousDayVolume = signal?.previousDayVolume || 1000;
  const maxDailyVolume = Math.floor(previousDayVolume * 0.1);

  // Fetch stop-loss position when popup opens
  useEffect(() => {
    const fetchPosition = async () => {
      if (signal && isOpen && token) {
        setLoading(true);
        try {
          const response = await fetch(`${API_BASE_URL}/stop-loss/position/${signal.symbol}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (response.ok) {
            const data = await response.json();
            if (data.has_position) {
              setSlPosition(data.position);
            } else {
              // No position exists, create one from signal
              const createResponse = await fetch(`${API_BASE_URL}/stop-loss/create`, {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                  symbol: signal.symbol,
                  quantity: signal.quantity,
                  entry_price: signal.buyPrice || signal.clPrice,
                  stop_loss_price: signal.stopLoss || signal.clPrice * 0.9
                })
              });
              if (createResponse.ok) {
                const newData = await createResponse.json();
                // Fetch again to get full position
                const refetch = await fetch(`${API_BASE_URL}/stop-loss/position/${signal.symbol}`, {
                  headers: { 'Authorization': `Bearer ${token}` }
                });
                const refetchData = await refetch.json();
                setSlPosition(refetchData.position);
              }
            }
          }
        } catch (error) {
          console.error('Error fetching position:', error);
        } finally {
          setLoading(false);
        }
      } else if (signal && isOpen && !token) {
        // Guest mode - use signal data directly
        setSlPosition({
          total_quantity: signal.quantity,
          quantity_sold: 0,
          remaining_quantity: signal.quantity,
          sold_today: 0
        });
      }
    };
    fetchPosition();
  }, [signal, isOpen, token]);

  // Reset form when position loads
  useEffect(() => {
    if (signal && slPosition) {
      setPrice(signal.clPrice);
      setQuantity(0);
      setAmount(0);
      setValidationError('');
    }
  }, [signal, slPosition]);

  // Calculate amount and validate
  useEffect(() => {
    if (!slPosition) return;
    
    setAmount(quantity * price);
    
    const soldToday = slPosition.sold_today || 0;
    const remainingTodayLimit = maxDailyVolume - soldToday;
    const availableToSell = slPosition.remaining_quantity;
    
    if (quantity > 0 && quantity < 10) {
      setValidationError('Quantity less than 10 will be handled as Odd Lot manually');
    } else if (quantity > remainingTodayLimit) {
      setValidationError(`Cannot sell more than ${remainingTodayLimit} shares today (Already sold today: ${soldToday}/${maxDailyVolume})`);
    } else if (quantity > availableToSell) {
      setValidationError(`Cannot sell more than available: ${availableToSell} (Total sold: ${slPosition.quantity_sold}/${slPosition.total_quantity})`);
    } else {
      setValidationError('');
    }
  }, [quantity, price, maxDailyVolume, slPosition]);

  const handleConfirm = async () => {
    if (!slPosition) {
      alert('Position data not loaded');
      return;
    }
    
    if (quantity <= 0) {
      alert('Please enter a valid quantity');
      return;
    }
    
    const soldToday = slPosition.sold_today || 0;
    const remainingTodayLimit = maxDailyVolume - soldToday;
    const availableToSell = slPosition.remaining_quantity;
    
    if (quantity > remainingTodayLimit) {
      alert(`Cannot sell more than ${remainingTodayLimit} shares today (Already sold: ${soldToday})`);
      return;
    }
    if (quantity > availableToSell) {
      alert(`Cannot sell more than available: ${availableToSell} shares`);
      return;
    }
    
    if (quantity < 10) {
      if (!window.confirm(`This quantity (${quantity}) will be handled as an Odd Lot manually. Continue?`)) {
        return;
      }
    }
    
    if (token) {
      try {
        setLoading(true);
        const orderData = {
          symbol: signal.symbol,
          quantity: parseInt(quantity),
          price: parseFloat(price),
          order_type: 'SELL'
        };
        
        const response = await fetch(`${API_BASE_URL}/orders/book-order`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(orderData)
        });

        if (!response.ok) {
          throw new Error('Failed to book order');
        }
      } catch (error) {
        alert('Error booking sell order: ' + error.message);
        setLoading(false);
        return;
      } finally {
        setLoading(false);
      }
    }
    
    onConfirm({
      ...signal,
      saleQuantity: parseInt(quantity),
      salePrice: parseFloat(price),
      saleAmount: amount,
      isOddLot: quantity < 10
    });
    onClose();
  };

  if (!isOpen || !signal) return null;
  if (!slPosition) return <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center"><div className="text-white">Loading...</div></div>;
  
  const soldToday = slPosition.sold_today || 0;
  const remainingTodayLimit = maxDailyVolume - soldToday;
  const availableToSell = slPosition.remaining_quantity;
  const totalSold = slPosition.quantity_sold;
  const needToSell = slPosition.total_quantity;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-8 w-full max-w-md shadow-2xl">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-800">Book Sell Order</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors"
          >
            ×
          </button>
        </div>

        <div className="mb-6">
          <div className="bg-gradient-to-br from-red-50 to-rose-50 p-4 rounded-xl border border-red-200">
            <div className="flex items-center mb-2">
              <span className="font-bold text-red-800 text-xl">{signal.symbol}</span>
              <span className="ml-2 text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full font-medium">
                SL Hit
              </span>
            </div>
            <div className="text-sm text-red-700 space-y-1">
              <div><span className="font-medium">Total Need to Sell:</span> {needToSell} shares</div>
              <div><span className="font-medium">Already Sold:</span> {totalSold} shares</div>
              <div><span className="font-medium">Available to Sell:</span> {availableToSell} shares</div>
              <div className="pt-2 border-t border-red-300 mt-2">
                <div><span className="font-medium">Max Today (10% limit):</span> {maxDailyVolume} shares</div>
                <div><span className="font-medium">Sold Today:</span> {soldToday} shares</div>
                <div><span className="font-medium">Can Sell Today:</span> {Math.min(remainingTodayLimit, availableToSell)} shares</div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Sell Quantity (Max Today: {Math.min(remainingTodayLimit, availableToSell)})
            </label>
            <input
              type="number"
              min="1"
              max={Math.min(remainingTodayLimit, availableToSell)}
              value={quantity}
              onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
              disabled={loading}
              className={`w-full border-2 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:border-transparent ${
                validationError.includes('❌') 
                  ? 'border-red-300 focus:ring-red-500' 
                  : validationError.includes('⚠️')
                  ? 'border-yellow-300 focus:ring-yellow-500'
                  : 'border-gray-200 focus:ring-red-500'
              }`}
            />
            <div className="text-xs text-gray-600 mt-1 space-y-1">
              <div>• Can sell today: <span className="font-semibold">1 to {Math.min(remainingTodayLimit, availableToSell)}</span> shares</div>
              <div>• Less than 10 qty → Odd Lot (manual handling)</div>
            </div>
          </div>

          {validationError && (
            <div className={`p-3 rounded-xl text-xs font-medium ${
              validationError.includes('❌') 
                ? 'bg-red-50 border border-red-200 text-red-700'
                : 'bg-yellow-50 border border-yellow-200 text-yellow-700'
            }`}>
              {validationError}
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Price (₹)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={price}
              onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
              disabled={loading}
              className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Total Amount</label>
            <div className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm bg-gray-50 font-mono font-semibold text-red-800">
              ₹{(amount || 0).toLocaleString()}
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-xl p-3">
            <div className="text-xs text-blue-700 font-medium space-y-1">
              <div>📊 <span className="font-semibold">Summary</span></div>
              <div>From {availableToSell} available, selling {quantity || 0} shares today</div>
              <div>Remaining after sale: {availableToSell - (quantity || 0)} shares</div>
              {soldToday > 0 && (
                <div className="pt-1 border-t border-blue-300 mt-1">
                  <span className="text-blue-600">Already sold today: {soldToday} shares</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-4 mt-8">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-6 py-3 text-gray-600 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-colors font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={quantity <= 0 || validationError.includes('❌') || loading}
            className={`px-6 py-3 rounded-xl transition-all duration-200 font-medium shadow-lg hover:shadow-xl ${
              quantity <= 0 || validationError.includes('❌') || loading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-red-500 to-rose-600 text-white hover:from-red-600 hover:to-rose-700'
            }`}
          >
            {loading ? 'Booking...' : 'Book Sell Order'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Book Buy Popup Component
const BookBuyPopup = ({ signal, isOpen, onClose, onConfirm, token }) => {
  const [quantity, setQuantity] = useState(0);
  const [price, setPrice] = useState(0);
  const [amount, setAmount] = useState(0);
  const [validationError, setValidationError] = useState('');
  const [loading, setLoading] = useState(false);
  const [orderHistory, setOrderHistory] = useState(null);

  const previousDayVolume = signal?.previousDayVolume || 2000;
  const maxDailyVolume = Math.floor(previousDayVolume * 0.1);
  const recommendedQty = signal?.quantity || 0;
  const industryRank = signal?.industryRank || '#N/A';
  const industry = signal?.industry || 'N/A';

  // Fetch order history when popup opens
  useEffect(() => {
    const fetchHistory = async () => {
      if (signal && isOpen && token) {
        setLoading(true);
        try {
          const response = await fetch(`${API_BASE_URL}/orders/history/${signal.symbol}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (response.ok) {
            const history = await response.json();
            setOrderHistory(history);
          } else {
            setOrderHistory({ total_bought: 0, total_sold: 0, transactions: [] });
          }
        } catch (error) {
          console.error('Error fetching history:', error);
          setOrderHistory({ total_bought: 0, total_sold: 0, transactions: [] });
        } finally {
          setLoading(false);
        }
      } else if (signal && isOpen && !token) {
        setOrderHistory({ total_bought: 0, total_sold: 0, transactions: [] });
      }
    };
    fetchHistory();
  }, [signal, isOpen, token]);

  // Initialize form when signal changes
  useEffect(() => {
    if (signal && orderHistory) {
      const initialPrice = parseFloat(signal.close) || 0;
      setPrice(initialPrice);
      
      const boughtToday = orderHistory?.transactions
        ?.filter(t => {
          const txDate = new Date(t.timestamp);
          const today = new Date();
          return t.type === 'BUY' && txDate.toDateString() === today.toDateString();
        })
        .reduce((sum, t) => sum + t.quantity, 0) || 0;
      
      const remainingToday = maxDailyVolume - boughtToday;
      const suggestedQty = Math.min(recommendedQty, remainingToday);
      
      setQuantity(suggestedQty > 0 ? suggestedQty : 0); 
      setAmount(initialPrice * (suggestedQty > 0 ? suggestedQty : 0));
      setValidationError('');
    }
  }, [signal, recommendedQty, maxDailyVolume, orderHistory]);

  // Validate on quantity/price change
  useEffect(() => {
    const validQuantity = parseInt(quantity) || 0;
    const validPrice = parseFloat(price) || 0;
    setAmount(validQuantity * validPrice);
    
    const boughtToday = orderHistory?.transactions
      ?.filter(t => {
        const txDate = new Date(t.timestamp);
        const today = new Date();
        return t.type === 'BUY' && txDate.toDateString() === today.toDateString();
      })
      .reduce((sum, t) => sum + t.quantity, 0) || 0;
    
    const remainingToday = maxDailyVolume - boughtToday;
    
    if (validQuantity > 0 && validPrice < 10) {
      setValidationError(`Cannot buy: Minimum price per share must be ≥ ₹10 (currently ₹${validPrice.toFixed(2)})`);
    } else if (validQuantity > remainingToday) {
      setValidationError(`Cannot buy more than ${remainingToday} shares today (Already bought: ${boughtToday}/${maxDailyVolume})`);
    } else if (validQuantity > recommendedQty && validQuantity <= remainingToday) {
      setValidationError(`Buying more than recommended quantity (${recommendedQty}). Max limit today: ${remainingToday}`);
    } else if (validQuantity > 0 && validQuantity < 10) {
      setValidationError('Buying less than 10 shares - consider buying at least 10 for better execution');
    } else {
      setValidationError('');
    }
  }, [quantity, price, maxDailyVolume, recommendedQty, orderHistory]);

  const handleConfirm = async () => {
    const validQuantity = parseInt(quantity) || 0;
    const validPrice = parseFloat(price) || 0;
    
    if (validQuantity <= 0) {
      alert('Please enter a valid quantity');
      return;
    }
    
    if (validPrice < 10) {
      alert(`Cannot buy: Price per quantity must be at least ₹10. Current: ₹${validPrice.toFixed(2)}`);
      return;
    }
    
    const boughtToday = orderHistory?.transactions
      ?.filter(t => {
        const txDate = new Date(t.timestamp);
        const today = new Date();
        return t.type === 'BUY' && txDate.toDateString() === today.toDateString();
      })
      .reduce((sum, t) => sum + t.quantity, 0) || 0;
    
    const remainingToday = maxDailyVolume - boughtToday;
    
    if (validQuantity > remainingToday) {
      alert(`Cannot buy more than ${remainingToday} shares today (Already bought: ${boughtToday})`);
      return;
    }
    
    if (validQuantity < 10) {
      if (!window.confirm(`Buying only ${validQuantity} shares. It's recommended to buy at least 10 shares. Continue anyway?`)) {
        return;
      }
    }
    
    if (token) {
      try {
        setLoading(true);
        const orderData = {
          symbol: signal.symbol,
          quantity: validQuantity,
          price: validPrice,
          order_type: 'BUY',
          user_email: ''
        };
        
        const response = await fetch(`${API_BASE_URL}/orders/book-order`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(orderData)
        });

        if (!response.ok) {
          throw new Error('Failed to book order');
        }
      } catch (error) {
        alert('Error booking order: ' + error.message);
        setLoading(false);
        return;
      } finally {
        setLoading(false);
      }
    }
    
    onConfirm({
      ...signal,
      quantity: validQuantity,
      close: validPrice,
      amount: validQuantity * validPrice,
      previousDayVolume
    });
    onClose();
  };

  if (!isOpen || !signal) return null;

  const currentQuantity = parseInt(quantity) || 0;
  
  const boughtToday = orderHistory?.transactions
    ?.filter(t => {
      const txDate = new Date(t.timestamp);
      const today = new Date();
      return t.type === 'BUY' && txDate.toDateString() === today.toDateString();
    })
    .reduce((sum, t) => sum + t.quantity, 0) || 0;
  
  const remainingToday = maxDailyVolume - boughtToday;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-8 w-full max-w-md shadow-2xl">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-800">Book Buy Order</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors"
          >
            ×
          </button>
        </div>

        <div className="mb-6">
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200">
            <div className="flex items-center mb-2">
              <span className="font-bold text-blue-800 text-xl">{signal.symbol || 'STOCK'}</span>
              <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">
                {industry}
              </span>
            </div>
            <div className="text-sm text-blue-700 space-y-1">
              <div><span className="font-medium">Industry Rank:</span> {industryRank}</div>
              <div><span className="font-medium">Max Shares Today:</span> {maxDailyVolume} shares (10% Daily Volume Limit)</div>
              {boughtToday > 0 && (
                <div className="pt-2 border-t border-blue-300 mt-2">
                  <div><span className="font-medium">Already Bought Today:</span> {boughtToday} shares</div>
                  <div><span className="font-medium">Can Buy Today:</span> {remainingToday} shares</div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Quantity (Max Today: {remainingToday})
            </label>
            <input
              type="number"
              min="1"
              max={remainingToday}
              value={quantity}
              onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
              disabled={loading}
              className={`w-full border-2 rounded-xl px-4 py-3 text-lg font-mono focus:outline-none focus:ring-2 focus:border-transparent ${
                validationError.includes('❌') 
                  ? 'border-red-300 focus:ring-red-500' 
                  : validationError.includes('⚠️')
                  ? 'border-yellow-300 focus:ring-yellow-500'
                  : 'border-gray-200 focus:ring-blue-500'
              }`}
            />
            <div className="text-xs text-gray-600 mt-1 space-y-1">
              <div>• Min Order Size: <span className="font-semibold">₹10 per share</span></div>
              {boughtToday > 0 && (
                <div>• Already bought today: <span className="font-semibold">{boughtToday} shares</span></div>
              )}
            </div>
          </div>

          {validationError && (
            <div className={`p-3 rounded-xl text-xs font-medium ${
              validationError.includes('❌') 
                ? 'bg-red-50 border border-red-200 text-red-700'
                : 'bg-yellow-50 border border-yellow-200 text-yellow-700'
            }`}>
              {validationError}
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Buy Price (₹)</label>
            <input
              type="number"
              step="0.01"
              min="10"
              value={price}
              onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
              disabled={loading}
              className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-lg font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Total Amount</label>
            <div className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-lg bg-gray-50 font-mono font-extrabold text-blue-800">
              ₹{(amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-xl p-3">
            <div className="text-xs text-green-700 font-medium space-y-1">
              <div className="text-sm font-bold">Summary</div>
              <div>From {maxDailyVolume} max qty, today buying {currentQuantity}</div>
              {boughtToday > 0 && (
                <div className="pt-1 border-t border-green-300 mt-1">
                  <span className="text-green-600">Already bought today: {boughtToday} shares</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-4 mt-8">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-6 py-3 text-gray-600 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-colors font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={currentQuantity <= 0 || validationError.includes('❌') || loading}
            className={`px-6 py-3 rounded-xl transition-all duration-200 font-medium shadow-lg hover:shadow-xl ${
              currentQuantity <= 0 || validationError.includes('❌') || loading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:from-green-600 hover:to-emerald-700'
            }`}
          >
            {loading ? 'Booking...' : 'Book Buy Order'}
          </button>
        </div>
      </div>
    </div>
  );
};


// Buy Signals Ticker Component
const BuySignalsTicker = ({ signals, setSignals }) => {
    const buySignals = signals.filter(signal => signal.recommendation === "BUY");
    const shouldScroll = buySignals.length > 5;

    const [priceHistory, setPriceHistory] = useState({});

    useEffect(() => {
        const interval = setInterval(() => {
            setSignals(prevSignals => prevSignals.map(signal => {
                if (signal.recommendation === "BUY") {
                    const change = (Math.random() - 0.5) * 5;
                    const newPrice = Math.max(0, parseFloat(signal.close) + change).toFixed(2);
                    const oldPrice = priceHistory[signal.symbol];

                    if (oldPrice !== undefined) {
                        if (parseFloat(newPrice) > parseFloat(oldPrice)) {
                            signal.color = "green";
                        } else if (parseFloat(newPrice) < parseFloat(oldPrice)) {
                            signal.color = "red";
                        } else {
                            signal.color = "gray";
                        }
                    } else {
                        signal.color = "gray";
                    }
                    setPriceHistory(prev => ({ ...prev, [signal.symbol]: newPrice }));
                    return { ...signal, close: newPrice };
                }
                return signal;
            }));
        }, 2000);

        return () => clearInterval(interval);
    }, [signals, priceHistory, setSignals]);

    return (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-xl p-4 mb-6 overflow-hidden">
            <div className="flex items-center mb-2">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                <h3 className="text-sm font-bold text-green-800">Buy Signals Today</h3>
                <span className="ml-2 bg-green-100 text-green-700 px-2 py-1 rounded-full text-xs font-medium">
                    {buySignals.length} Active
                </span>
            </div>

            <div className="relative">
                {buySignals.length > 0 ? (
                    <div className={`flex ${shouldScroll ? 'animate-scroll-rtl' : 'justify-start'} whitespace-nowrap`}>
                        <div className="flex space-x-6">
                            {buySignals.map((signal, index) => (
                                <div
                                    key={index}
                                    className="inline-flex items-center bg-white/80 backdrop-blur-sm border border-green-200 rounded-lg px-4 py-2 shadow-sm hover:shadow-md transition-all duration-200"
                                >
                                    <div className="flex flex-col items-start">
                                        <div className="flex items-center mb-1">
                                            <span className="font-bold text-green-800 text-lg mr-2">
                                                {signal.symbol}
                                            </span>
                                            <span
                                                className={`font-semibold text-lg ${
                                                    signal.color === "green" ? "text-green-600" :
                                                    signal.color === "red" ? "text-red-600" : "text-gray-600"
                                                }`}
                                            >
                                                (₹{signal.close})
                                            </span>
                                        </div>
                                    </div>
                                    <div className="ml-3 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                                </div>
                            ))}
                            {shouldScroll && buySignals.map((signal, index) => (
                                <div
                                    key={`duplicate-${index}`}
                                    className="inline-flex items-center bg-white/80 backdrop-blur-sm border border-green-200 rounded-lg px-4 py-2 shadow-sm hover:shadow-md transition-all duration-200"
                                >
                                    <div className="flex flex-col items-start">
                                        <div className="flex items-center mb-1">
                                            <span className="font-bold text-green-800 text-lg mr-2">
                                                {signal.symbol}
                                            </span>
                                            <span
                                                className={`font-semibold text-lg ${
                                                    signal.color === "green" ? "text-green-600" :
                                                    signal.color === "red" ? "text-red-600" : "text-gray-600"
                                                }`}
                                            >
                                                (₹{signal.close})
                                            </span>
                                        </div>
                                    </div>
                                    <div className="ml-3 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="text-center py-4">
                        <span className="text-green-600 text-sm">No buy signals available today</span>
                    </div>
                )}
            </div>
        </div>
    );
};

// Enhanced Executor component
const Executor = ({
  autoExecutor,
  setAutoExecutor,
  buySignals,
  onBookBuyFromSignal,
  sellSignals,
  executorLogs,
  onBookSellFromSignal
}) => {
  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 p-6 hover:shadow-xl transition-all duration-300 h-full">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-gray-800 flex items-center">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-xl flex items-center justify-center text-sm font-bold mr-4 shadow-sm">
            1
          </div>
          Executor
        </h2>
        <div className="flex items-center space-x-3">
          <span className="text-sm font-medium text-gray-600">Auto Mode:</span>
          <button
            onClick={() => setAutoExecutor(!autoExecutor)}
            className={`relative inline-flex h-7 w-12 items-center rounded-full transition-all duration-300 shadow-inner ${
              autoExecutor ? "bg-gradient-to-r from-green-400 to-emerald-500" : "bg-gray-300"
            }`}
          >
            <span
              className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-lg transition-transform duration-300 ${
                autoExecutor ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
          <span className={`text-sm font-bold ${autoExecutor ? "text-green-600" : "text-gray-500"}`}>
            {autoExecutor ? "ON" : "OFF"}
          </span>
        </div>
      </div>

      <div className="mb-4 p-4 bg-gradient-to-br from-gray-50 to-slate-50 border border-gray-200 rounded-xl shadow-sm">
        <h4 className="text-sm font-bold text-gray-800 mb-3 flex items-center">
          <div className="w-2 h-2 bg-gray-500 rounded-full mr-2"></div>
          Activity History
        </h4>
        <div className="space-y-2 max-h-32 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
          {executorLogs && executorLogs.length > 0 ? (
            executorLogs.map((log, i) => (
              <div
                key={i}
                className={`p-2 rounded-lg text-xs border transition-all duration-200 ${
                  log.type === 'sell_signal'
                    ? 'bg-red-50 border-red-200 text-red-800'
                    : log.type === 'book_buy'
                    ? 'bg-green-50 border-green-200 text-green-800'
                    : log.type === 'confirmed'
                    ? 'bg-purple-50 border-purple-200 text-purple-800'
                    : 'bg-gray-50 border-gray-200 text-gray-800'
                }`}
              >
                <div className="font-medium mb-1">{log.message}</div>
                <div className="text-xs opacity-75">{log.timestamp}</div>
              </div>
            ))
          ) : (
            <div className="text-center py-4 text-gray-500 text-xs">
              No activity logs yet
            </div>
          )}
        </div>
      </div>

      {sellSignals && sellSignals.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-bold text-red-800 mb-3 flex items-center">
            <div className="w-2 h-2 bg-red-500 rounded-full mr-2 animate-pulse"></div>
            Risk - Sell Signals
          </h4>
          <div className="space-y-3">
            {sellSignals.map((signal, i) => (
              <div
                key={i}
                className="p-4 bg-gradient-to-br from-red-50 to-rose-50 border border-red-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-200"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <span className="font-bold text-red-800 text-lg">{signal.symbol}</span>
                      <span className="mx-2 text-red-600">@</span>
                      <span className="font-mono text-red-800 font-semibold">₹{signal.clPrice}</span>
                      <span className="ml-2 text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full font-medium">
                        SL Hit
                      </span>
                    </div>
                    <div className="text-sm text-red-700 mb-1">
                      <span className="font-medium">Need to sell remaining Qty:</span> {signal.quantity}
                    </div>
                  </div>
                  <button
                    onClick={() => onBookSellFromSignal(signal)}
                    className="bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 shadow-sm hover:shadow-md"
                  >
                    Book Sell
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {buySignals && buySignals.filter((signal) => signal.recommendation === "BUY").length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-bold text-blue-800 mb-3 flex items-center">
            <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
            Today's Buy Signals - Action Required
          </h4>
          <div className="space-y-3">
            {buySignals
              .filter((signal) => signal.recommendation === "BUY")
              .map((signal, i) => {
                const totalAmount = signal.close * signal.quantity;
                const boughtQty = Math.floor(signal.quantity * 0.5);
                const boughtAmount = signal.close * boughtQty;
                
                return (
                  <div
                    key={i}
                    className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-200"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center mb-2">
                          <span className="font-bold text-blue-800 text-lg">{signal.symbol}</span>
                          <span className="mx-2 text-blue-600">@</span>
                          <span className="font-mono text-blue-800 font-semibold">₹{signal.close}</span>
                          <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">
                            {signal.industry}
                          </span>
                        </div>
                        <div className="text-xs text-blue-600 mt-2">
                          (₹{boughtAmount.toLocaleString()}/{boughtQty})
                        </div>
                      </div>
                      <div className="flex flex-col space-y-2 ml-4">
                        <button
                          onClick={() => onBookBuyFromSignal(signal)}
                          className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 shadow-sm hover:shadow-md"
                        >
                          Book Buy
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
};

// Biller Component
const Biller = ({ billerPositions, onSellFromBiller }) => {
  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 p-6 hover:shadow-xl transition-all duration-300">
      <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
        <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-violet-600 text-white rounded-xl flex items-center justify-center text-sm font-bold mr-4 shadow-sm">
          6
        </div>
        Biller
      </h2>
      <div className="h-full overflow-y-auto">
        {billerPositions && billerPositions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-gradient-to-r from-purple-50 to-violet-50 border-b border-purple-200">
                  <th className="text-left p-2 font-semibold text-purple-800">Script</th>
                  <th className="text-left p-2 font-semibold text-purple-800">ID</th>
                  <th className="text-left p-2 font-semibold text-purple-800">Qty</th>
                  <th className="text-left p-2 font-semibold text-purple-800">Buy Price</th>
                  <th className="text-left p-2 font-semibold text-purple-800">Current Price</th>
                  <th className="text-left p-2 font-semibold text-purple-800">SL Price</th>
                  <th className="text-left p-2 font-semibold text-purple-800">P&L %</th>
                  <th className="text-left p-2 font-semibold text-purple-800">Status / Action</th>
                </tr>
              </thead>
              <tbody>
                {billerPositions.map((position, i) => {
                  const plPercent = ((position.clPrice - position.buyPrice) / position.buyPrice * 100);
                  const isAtRisk = position.clPrice < position.slPrice;

                  return (
                    <tr key={i} className={`border-b border-purple-100 hover:opacity-90 transition-colors ${isAtRisk ? 'bg-red-50/50' : ''}`}>
                      <td className="p-2 font-bold text-purple-800">{position.symbol}</td>
                      <td className="p-2 text-purple-700 font-mono text-xs">{position.id}</td>
                      <td className="p-2 text-purple-700 font-semibold">{position.quantity}</td>
                      <td className="p-2 text-purple-700 font-mono text-xs">₹{position.buyPrice}</td>
                      <td className="p-2 text-purple-700 font-mono text-xs">₹{position.clPrice}</td>
                      <td className="p-2 text-purple-700 font-mono text-xs">₹{position.slPrice.toFixed(2)}</td>
                      <td className={`p-2 font-semibold text-xs ${plPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {plPercent >= 0 ? '+' : ''}{plPercent.toFixed(2)}%
                      </td>
                      <td className="p-2">
                        {isAtRisk ? (
                          <button
                            onClick={() => onSellFromBiller(position)}
                            className="bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 text-white px-3 py-1 rounded-lg text-xs font-semibold transition-all duration-200 shadow-sm hover:shadow-md"
                          >
                            SELL
                          </button>
                        ) : (
                          <span className="px-2 py-1 rounded-full text-xs font-bold border bg-green-100 text-green-700 border-green-200">
                            SAFE
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <span className="text-2xl">📋</span>
            </div>
            <p className="text-center">No biller positions</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Odd Lot Balance Component
const OddLotBalance = ({ oddLots }) => {
  const totalAmount = oddLots.reduce((sum, lot) => {
    const netAmount = (lot.quantity * lot.price) - (lot.charges || 0);
    return sum + netAmount;
  }, 0);
  
  return (
    <div className="mt-4 p-4 bg-gradient-to-br from-yellow-50 to-amber-50 border border-yellow-200 rounded-xl shadow-sm">
      <h4 className="text-sm font-bold text-yellow-800 mb-3 flex items-center">
        <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></div>
        Odd Lot Balance
      </h4>
      
      {oddLots && oddLots.length > 0 ? (
        <div className="text-center p-4 bg-white/80 rounded-lg border border-yellow-200">
          <div className="text-2xl font-bold text-yellow-800 mb-1">
            ₹{totalAmount.toLocaleString()}
          </div>
          <div className="text-xs text-yellow-600">Total Odd Lot Amount</div>
        </div>
      ) : (
        <div className="text-center py-2 text-yellow-600 text-sm">
          No odd lots available
        </div>
      )}
    </div>
  );
};

// Section Card Component
const SectionCard = ({ number, title, children, gradient = "from-gray-500 to-gray-600", bgColor = "bg-white" }) => (
  <div className={`${bgColor} rounded-2xl shadow-lg border border-gray-200/50 p-6 hover:shadow-xl transition-all duration-300 h-full`}>
    <h2 className="text-xl font-bold mb-4 text-gray-800 flex items-center">
      <div className={`w-8 h-8 bg-gradient-to-br ${gradient} text-white rounded-xl flex items-center justify-center text-sm font-bold mr-4 shadow-sm`}>{number}</div>
      {title}
    </h2>
    <div className="h-[calc(100%-4rem)]">{children}</div>
  </div>
);

function TradingDashboard() {
  const { token } = useAuth(); 
  const [realSignals, setRealSignals] = useState([]);
  const [signalsLoading, setSignalsLoading] = useState(false);
  const [signalsError, setSignalsError] = useState(null);
  const [lastSignalUpdate, setLastSignalUpdate] = useState(null);
  const [signals, setSignals] = useState([]);
  const [executorLogs, setExecutorLogs] = useState([]);
  const [inTransit, setInTransit] = useState([]);
  const [risk, setRisk] = useState([]);
  const [billerPositions, setBillerPositions] = useState([]);
  const [salesInTransit, setSalesInTransit] = useState([]);
  const [cashBalance, setCashBalance] = useState(1000000);
  const [sellSignals, setSellSignals] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [cumulativeProfitLoss, setCumulativeProfitLoss] = useState(0);
  const [oddLots, setOddLots] = useState([]);

  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [showBookBuyPopup, setShowBookBuyPopup] = useState(false);
  const [showBookSellPopup, setShowBookSellPopup] = useState(false);
  const [selectedSignal, setSelectedSignal] = useState(null);

  const [autoExecutor, setAutoExecutor] = useState(false);
  const [marketCap, setMarketCap] = useState("NEPSE");

  const [showAddIndustry, setShowAddIndustry] = useState(false);
  const [newIndustry, setNewIndustry] = useState({ sector: '', rank: 1, weightage: 0, enabled: true });

  const technicalIndicators = ["RSI", "MA", "MACD", "Volume"];

  const [industryPreferences, setIndustryPreferences] = useState([
    { sector: "Banking", rank: 1, weightage: 25, enabled: true },
    { sector: "Hydropower", rank: 2, weightage: 20, enabled: true },
    { sector: "Insurance", rank: 3, weightage: 15, enabled: true },
    { sector: "Hotels & Tourism", rank: 4, weightage: 12, enabled: false },
    { sector: "Manufacturing", rank: 5, weightage: 10, enabled: true },
    { sector: "Microfinance", rank: 6, weightage: 8, enabled: false },
    { sector: "Others", rank: 7, weightage: 10, enabled: true }
  ]);

  const [riskSettings, setRiskSettings] = useState({
    amount: "50000",
    initialSL: "5",
    executionDays: "3",
    portfolioSize: "1000000",
    maxPositioning: "20",
    minPrice: "10",
    maxPrice: "5000",
    slStage: "7"
  });

   // Function to fetch real NEPSE signals
 const fetchRealSignals = async () => {
  if (!token) return;
  
  try {
    setSignalsLoading(true);
    setSignalsError(null);
    const data = await apiService.getTodaySignals(token);
    
    console.log('Backend Response:', data);
    
    // Process signals with proper field mapping
    const processedSignals = (data.signals || []).map(signal => ({
      symbol: signal.symbol || '',
      close: signal.price || signal.close || 0,  // Backend sends "price"
      recommendation: signal.signal || 'REJECT',  // Backend sends "signal"
      quantity: signal.quantity || 100,
      industry: signal.industry || 'N/A',
      industryRank: signal.industryRank || '#N/A',
      previousDayVolume: signal.previousDayVolume || signal.prev_volume || 2000,
      
      // Technical indicators
      rsi: signal.rsi,
      ma50: signal.ma50,
      macd: signal.macd,
      macd_signal: signal.macd_signal,
      volume: signal.volume,
      prev_volume: signal.prev_volume,
      
      // Additional fields
      change: signal.change,
      date: signal.date,
      rsi_ok: signal.rsi_ok,
      ma_ok: signal.ma_ok,
      macd_ok: signal.macd_ok,
      volume_ok: signal.volume_ok
    }));
    
    console.log('Processed signals:', processedSignals);
    
    setRealSignals(processedSignals);
    setSignals(processedSignals);
    setLastSignalUpdate(new Date());
    
    const buyCount = processedSignals.filter(s => s.recommendation === 'BUY').length;
    setExecutorLogs(prev => [...prev, {
      message: `Real signals loaded - ${buyCount} buy signals, ${processedSignals.length - buyCount} rejected`,
      timestamp: new Date().toLocaleTimeString(),
      type: 'system'
    }]);
    
  } catch (err) {
    console.error('Error fetching signals:', err);
    setSignalsError(err.message);
    const mockSignals = generatePortfolioBasedSignals();
    setSignals(mockSignals);
  } finally {
    setSignalsLoading(false);
  }
};

  // Function to refresh signals
  const handleRefreshSignals = async () => {
    if (!token) return;
    
    try {
      setSignalsLoading(true);
      setSignalsError(null);
      await apiService.refreshSignals(token);
      await fetchRealSignals();
      
      setExecutorLogs(prev => [...prev, {
        message: 'Signals refreshed successfully from NEPSE pipeline',
        timestamp: new Date().toLocaleTimeString(),
        type: 'system'
      }]);
    } catch (err) {
      console.error('Error refreshing signals:', err);
      setSignalsError(err.message);
      alert('Error refreshing signals: ' + err.message);
    } finally {
      setSignalsLoading(false);
    }
  };

  const generatePortfolioBasedSignals = () => {
    const enabledIndustries = industryPreferences.filter(ind => ind.enabled);
    const totalPortfolio = parseInt(riskSettings.portfolioSize);
    const maxPositionAmount = (totalPortfolio * parseInt(riskSettings.maxPositioning)) / 100;

    const mockStocks = [
      { symbol: "NABIL", industry: "Banking", price: 1200 },
      { symbol: "TSHL", industry: "Hydropower", price: 260 },
      { symbol: "NLIC", industry: "Insurance", price: 920 },
      { symbol: "OHL", industry: "Hotels & Tourism", price: 450 },
      { symbol: "BNHC", industry: "Manufacturing", price: 180 },
      { symbol: "CBBL", industry: "Banking", price: 280 }
    ];

    return mockStocks
      .filter(stock => enabledIndustries.find(ind => ind.sector === stock.industry))
      .map(stock => {
        const industry = enabledIndustries.find(ind => ind.sector === stock.industry);
        const portfolioWeight = Math.min(industry.weightage, parseInt(riskSettings.maxPositioning));
        const amount = Math.min((totalPortfolio * portfolioWeight) / 100, maxPositionAmount, parseInt(riskSettings.amount));
        const quantity = Math.floor(amount / stock.price);

        return {
          symbol: stock.symbol,
          close: stock.price,
          recommendation: Math.random() > 0.3 ? "BUY" : "REJECT",
          date: new Date().getDay() === 1 ? "Friday" : "Today",
          quantity,
          amount: quantity * stock.price,
          industry: stock.industry,
          industryRank: industry.rank,
          portfolioWeight
        };
      });
  };

  const checkForOddLots = (riskPositions) => {
    return riskPositions
      .filter(position => position.quantity >= 1 && position.quantity <= 5)
      .map(position => ({
        symbol: position.symbol,
        quantity: position.quantity,
        price: position.clPrice || position.avBuyPrice,
        charges: position.quantity * position.clPrice * 0.025,
        buyPrice: position.avBuyPrice
      }));
  };

  const consolidateRiskPositions = (positions) => {
    const consolidated = {};
    
    positions.forEach(position => {
      if (consolidated[position.symbol]) {
        const existing = consolidated[position.symbol];
        const totalQty = existing.quantity + position.quantity;
        const totalAmount = (existing.avBuyPrice * existing.quantity) + (position.buyPrice * position.quantity);
        
        consolidated[position.symbol] = {
          ...existing,
          quantity: totalQty,
          totalQuantity: totalQty,
          avBuyPrice: totalAmount / totalQty,
          amount: totalAmount,
          slPrice: Math.min(existing.slPrice, position.slPrice)
        };
      } else {
        consolidated[position.symbol] = {
          ...position,
          avBuyPrice: position.buyPrice,
          totalQuantity: position.quantity
        };
      }
    });
    
    return Object.values(consolidated);
  };

  const calculatePortfolioValue = () => {
    const riskValue = risk.reduce((sum, pos) => sum + (pos.amount || 0), 0);
    const oddLotValue = oddLots.reduce((sum, lot) => sum + (lot.quantity * lot.price), 0);
    return (cashBalance || 0) + riskValue + oddLotValue + (cumulativeProfitLoss || 0);
  };

  const checkRiskPositions = (positions) => {
    const sellSignals = positions
      .filter(position => position.clPrice < position.slPrice)
      .map(position => ({
        ...position,
        reason: "SL Hit"
      }));

    setSellSignals(sellSignals);

    if (sellSignals.length > 0) {
      const sellMessages = sellSignals.map(signal => ({
        message: `SELL signal ${signal.symbol} @ ₹${signal.clPrice} | Need to sell remaining Qty: ${signal.quantity} | SL Hit`,
        timestamp: new Date().toLocaleTimeString(),
        type: 'sell_signal'
      }));

      setExecutorLogs(prev => [...prev, ...sellMessages]);
    }
  };

  const generateBillerID = () => {
    return 'BIL' + Date.now().toString().slice(-6) + Math.floor(Math.random() * 100);
  };

  useEffect(() => {
  let portfolioSignals = []; 
  
  if (token) {
    fetchRealSignals();
  } else {
    // Load mock signals if no token
    portfolioSignals = generatePortfolioBasedSignals();
    setSignals(portfolioSignals);
  }
  
  setCashBalance(parseInt(riskSettings.portfolioSize));

  const mockRiskPositions = [
    {
      symbol: "NIFRA",
      quantity: 2,
      buyPrice: 200,
      clPrice: 180,
      slPrice: 190,
      confirmedAt: "2:30 PM",
      industry: "Banking",
      id: generateBillerID()
    },
    {
      symbol: "NIFRA",
      quantity: 150,
      buyPrice: 195,
      clPrice: 180,
      slPrice: 185.25,
      confirmedAt: "3:15 PM",
      industry: "Banking",
      id: generateBillerID()
    },
    {
      symbol: "GBIME",
      quantity: 3,
      buyPrice: 150,
      clPrice: 160,
      slPrice: 142.5,
      confirmedAt: "Yesterday",
      industry: "Banking",
      id: generateBillerID()
    },
    {
      symbol: "TSHL",
      quantity: 100,
      buyPrice: 260,
      clPrice: 255,
      slPrice: 247,
      confirmedAt: "Today",
      industry: "Hydropower",
      id: generateBillerID()
    }
  ];

  setBillerPositions(mockRiskPositions);
  
  const consolidatedRisk = consolidateRiskPositions(mockRiskPositions);
  setRisk(consolidatedRisk);
  
  const detectedOddLots = checkForOddLots(consolidatedRisk);
  setOddLots(detectedOddLots);
  
  checkRiskPositions(consolidatedRisk);

  const initialLogs = [
    {
      message: `System initialized - ${portfolioSignals.filter(s => s.recommendation === 'BUY').length} buy signals detected`, // ✅ NOW IT WORKS
      timestamp: new Date().toLocaleTimeString(),
      type: 'system'
    }
  ];
  setExecutorLogs(initialLogs);
}, [token, riskSettings.portfolioSize]); 

   // Refresh signals when preferences change
  useEffect(() => {
    if (!token) {
      const portfolioSignals = generatePortfolioBasedSignals();
      setSignals(portfolioSignals);
    }
  }, [riskSettings, industryPreferences]);

  const handleBookBuyFromSignal = (signal) => {
    setSelectedSignal(signal);
    setShowBookBuyPopup(true);
  };

  const handleBookSellFromSignal = (signal) => {
    setSelectedSignal(signal);
    setShowBookSellPopup(true);
  };

  const handleBookBuyConfirm = (orderDetails) => {
    const transitOrder = {
      ...orderDetails,
      transitDate: new Date().toLocaleString(),
      exactPrice: orderDetails.close,
      qty: orderDetails.quantity
    };

    const msg = `Buy order booked and sent to transit: ${orderDetails.symbol} @ ₹${orderDetails.close} | Qty: ${orderDetails.quantity} | Amount: ₹${(orderDetails.amount || 0).toLocaleString()}`;
    setExecutorLogs(prev => [...prev, { message: msg, timestamp: new Date().toLocaleTimeString(), type: 'book_buy' }]);

    setInTransit(prev => [...prev, transitOrder]);
    setCashBalance(prev => prev - orderDetails.amount);
  };

  const handleBookSellConfirm = (saleDetails) => {
    const saleOrder = {
      symbol: saleDetails.symbol,
      saleQuantity: saleDetails.saleQuantity,
      salePrice: saleDetails.salePrice,
      saleAmount: saleDetails.saleAmount,
      avBuyPrice: saleDetails.avBuyPrice || saleDetails.buyPrice,
      saleReason: "SL Hit - Manual Booking",
      transitDate: new Date().toLocaleString()
    };

    const msg = `Sell order booked and sent to transit: ${saleDetails.symbol} @ ₹${saleDetails.salePrice} | Qty: ${saleDetails.saleQuantity} | Amount: ₹${saleDetails.saleAmount.toLocaleString()}`;
    setExecutorLogs(prev => [...prev, { message: msg, timestamp: new Date().toLocaleTimeString(), type: 'book_sell' }]);

    setSalesInTransit(prev => [...prev, saleOrder]);
  };

  const handleConfirmToRisk = (order) => {
    const billerPosition = {
      symbol: order.symbol,
      quantity: order.qty || order.quantity,
      buyPrice: order.exactPrice || order.close,
      clPrice: order.exactPrice || order.close,
      slPrice: (order.exactPrice || order.close) * (1 - parseInt(riskSettings.initialSL) / 100),
      confirmedAt: new Date().toLocaleTimeString(),
      industry: order.industry || "Unknown",
      id: generateBillerID()
    };

    const msg = `Order confirmed and added to Risk/Biller monitoring: ${order.symbol} @ ₹${billerPosition.buyPrice} | SL: ₹${billerPosition.slPrice.toFixed(2)} | Qty: ${billerPosition.quantity}`;
    setExecutorLogs(prev => [...prev, { message: msg, timestamp: new Date().toLocaleTimeString(), type: 'confirmed' }]);

    setBillerPositions(prev => {
      const newBiller = [...prev, billerPosition];
      const consolidatedRisk = consolidateRiskPositions(newBiller);
      setRisk(consolidatedRisk);
      
      const detectedOddLots = checkForOddLots(consolidatedRisk);
      setOddLots(detectedOddLots);
      
      return newBiller;
    });
    
    setInTransit(prev => prev.filter(o => o.symbol !== order.symbol));

    setTimeout(() => {
      const consolidatedRisk = consolidateRiskPositions([...billerPositions, billerPosition]);
      checkRiskPositions(consolidatedRisk);
    }, 1000);
  };

  const handleSoldConfirm = (sale) => {
    const saleAmount = sale.saleQuantity * sale.salePrice;
    const profit = (sale.salePrice - sale.avBuyPrice) * sale.saleQuantity;

    const transaction = {
      symbol: sale.symbol,
      qty: sale.saleQuantity,
      profit,
      salePrice: sale.salePrice,
      buyPrice: sale.avBuyPrice,
      timestamp: new Date().toLocaleString(),
      reason: sale.saleReason
    };

    setTransactions(prev => [...prev, transaction]);
    setCumulativeProfitLoss(prev => prev + profit);

    const msg = `Sale completed: ${sale.symbol} @ ₹${sale.salePrice} | Qty: ${sale.saleQuantity} | P&L: ₹${profit.toFixed(2)}`;
    setExecutorLogs(prev => [...prev, { message: msg, timestamp: new Date().toLocaleTimeString(), type: 'sale_confirmed' }]);

    setSalesInTransit(prev => prev.filter(s => s.symbol !== sale.symbol));

    setCashBalance(prev => prev + saleAmount);
    setRisk(prev => prev.filter(p => p.symbol !== sale.symbol));
    setBillerPositions(prev => prev.filter(p => p.symbol !== sale.symbol));
  };

  const handleSellToTransit = (riskPosition) => {
    const salePrice = riskPosition.clPrice * 0.95;
    const saleOrder = {
      symbol: riskPosition.symbol,
      saleQuantity: riskPosition.quantity,
      salePrice,
      saleAmount: salePrice * riskPosition.quantity,
      avBuyPrice: riskPosition.avBuyPrice,
      saleReason: "SL Hit",
      transitDate: new Date().toLocaleString()
    };

    const msg = `Sale order sent to transit: ${riskPosition.symbol} @ ₹${salePrice.toFixed(2)} | Qty: ${riskPosition.quantity} | Reason: SL Hit`;
    setExecutorLogs(prev => [...prev, { message: msg, timestamp: new Date().toLocaleTimeString(), type: 'sell_transit' }]);

    setSalesInTransit(prev => [...prev, saleOrder]);
  };

  const handleSellFromBiller = (billerPosition) => {
    const salePrice = billerPosition.clPrice * 0.95;
    const saleOrder = {
      symbol: billerPosition.symbol,
      saleQuantity: billerPosition.quantity,
      salePrice,
      saleAmount: salePrice * billerPosition.quantity,
      avBuyPrice: billerPosition.buyPrice,
      saleReason: "SL Hit from Biller",
      transitDate: new Date().toLocaleString(),
      billerId: billerPosition.id
    };

    const msg = `Sale order sent to transit from Biller: ${billerPosition.symbol} (ID: ${billerPosition.id}) @ ₹${salePrice.toFixed(2)} | Qty: ${billerPosition.quantity}`;
    setExecutorLogs(prev => [...prev, { message: msg, timestamp: new Date().toLocaleTimeString(), type: 'sell_transit' }]);

    setSalesInTransit(prev => [...prev, saleOrder]);
  };

  const updateIndustryPreference = (index, field, value) => {
    setIndustryPreferences(prev =>
      prev.map((item, i) =>
        i === index ? { ...item, [field]: value } : item
      )
    );
  };

  const handleAddIndustry = () => {
    if (newIndustry.sector.trim()) {
      const maxRank = Math.max(...industryPreferences.map(ind => ind.rank), 0);
      const industryToAdd = {
        ...newIndustry,
        rank: maxRank + 1
      };
      setIndustryPreferences(prev => [...prev, industryToAdd]);
      setNewIndustry({ sector: '', rank: 1, weightage: 0, enabled: true });
      setShowAddIndustry(false);
    }
  };

  const removeIndustry = (index) => {
    setIndustryPreferences(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50">
      <div className="lg:hidden bg-white/80 backdrop-blur-md shadow-lg border-b border-gray-200/50 p-4 flex items-center justify-between sticky top-0 z-40">
        <h1 className="text-xl font-bold text-gray-800">Trading Pro</h1>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl shadow-md hover:shadow-lg transition-all duration-200"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>

      <div className="flex min-h-screen">
        <aside className={`
          fixed lg:relative z-50 lg:z-auto
          ${sidebarVisible ? 'w-80 lg:w-80 xl:w-96' : 'w-0 lg:w-12'}
          bg-white/95 backdrop-blur-md shadow-2xl border-r border-gray-200/50
          transform ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0
          transition-all duration-300 ease-in-out
          min-h-screen overflow-hidden
        `}>
          <div className="hidden lg:block absolute -right-6 top-4 z-10">
            <button
              onClick={() => setSidebarVisible(!sidebarVisible)}
              className={`
                w-12 h-12 bg-white shadow-lg border border-gray-200 rounded-r-xl
                flex items-center justify-center text-gray-600 hover:text-blue-600
                transition-all duration-300 hover:shadow-xl
                ${!sidebarVisible ? 'rounded-l-xl' : ''}
              `}
            >
              <svg
                className={`w-5 h-5 transition-transform duration-300 ${!sidebarVisible ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          </div>

          {sidebarVisible && (
            <>
              <div className="lg:hidden p-4 border-b flex justify-between items-center bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
                <h2 className="text-lg font-bold">Configuration</h2>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="p-4 lg:p-6 overflow-y-auto h-full">
                <h2 className="hidden lg:block text-xl font-bold text-gray-800 mb-6 pb-2 border-b border-gray-200">Configuration Panel</h2>

                <div className="space-y-6">
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200/50 shadow-sm">
                    <h3 className="font-bold text-gray-800 mb-3 flex items-center">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                      Market Configuration
                    </h3>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Market Selector</label>
                        <select
                          className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm"
                          value={marketCap}
                          onChange={(e) => setMarketCap(e.target.value)}
                        >
                          <option value="NEPSE">NEPSE</option>
                          <option value="OTHER">Other Markets</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-xl border border-green-200/50 shadow-sm">
                    <h3 className="font-bold text-gray-800 mb-3 flex items-center">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                      Technical Indicators
                    </h3>
                    <div className="grid grid-cols-2 gap-3">
                      {technicalIndicators.map((indicator) => (
                        <label key={indicator} className="flex items-center p-2 bg-white/60 rounded-lg hover:bg-white/80 transition-colors cursor-pointer">
                          <input type="checkbox" className="mr-3 w-4 h-4 text-green-600 rounded focus:ring-green-500" defaultChecked />
                          <span className="text-sm font-medium text-gray-700">{indicator}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-amber-50 to-yellow-50 p-4 rounded-xl border border-amber-200/50 shadow-sm">
                    <div className="flex justify-between items-center mb-3">
                      <h3 className="font-bold text-gray-800 flex items-center">
                        <div className="w-2 h-2 bg-amber-500 rounded-full mr-2"></div>
                        Industry Preferences
                      </h3>
                      <button
                        onClick={() => setShowAddIndustry(true)}
                        className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white px-3 py-1.5 rounded-lg text-sm font-semibold transition-all duration-200 shadow-sm hover:shadow-md"
                      >
                        + Add
                      </button>
                    </div>
                    <div className="space-y-3 max-h-64 overflow-y-auto">
                      {industryPreferences.map((industry, index) => (
                        <div key={industry.sector} className="bg-white/80 backdrop-blur-sm p-3 rounded-lg border border-amber-200/50 shadow-sm">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center">
                              <input
                                type="checkbox"
                                checked={industry.enabled}
                                onChange={(e) => updateIndustryPreference(index, 'enabled', e.target.checked)}
                                className="mr-2 w-4 h-4 text-amber-600 rounded focus:ring-amber-500"
                              />
                              <span className="font-semibold text-sm text-gray-800">{industry.sector}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full font-medium">#{industry.rank}</span>
                              <button
                                onClick={() => removeIndustry(index)}
                                className="text-red-500 hover:text-red-700 text-sm font-bold w-5 h-5 flex items-center justify-center rounded hover:bg-red-50 transition-colors"
                              >
                                ×
                              </button>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-2">
                            <div>
                              <label className="block text-xs font-medium text-gray-600 mb-1">Rank</label>
                              <input
                                type="number"
                                min="1"
                                max="20"
                                value={industry.rank}
                                onChange={(e) => updateIndustryPreference(index, 'rank', parseInt(e.target.value))}
                                className="w-full border-2 border-gray-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-medium text-gray-600 mb-1">Weight %</label>
                              <input
                                type="number"
                                min="0"
                                max="100"
                                value={industry.weightage}
                                onChange={(e) => updateIndustryPreference(index, 'weightage', parseInt(e.target.value))}
                                className="w-full border-2 border-gray-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-red-50 to-pink-50 p-4 rounded-xl border border-red-200/50 shadow-sm">
                    <h3 className="font-bold text-gray-800 mb-3 flex items-center">
                      <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
                      Risk Management
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <h4 className="text-sm font-bold text-gray-800 mb-3">Stop Loss Settings</h4>
                        <div className="grid grid-cols-2 gap-2 mb-3">
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Min Price</label>
                            <input
                              type="number"
                              className="w-full border-2 border-gray-200 rounded-lg px-2 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                              value={riskSettings.minPrice}
                              onChange={(e) => setRiskSettings({...riskSettings, minPrice: e.target.value})}
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Max Price</label>
                            <input
                              type="number"
                              className="w-full border-2 border-gray-200 rounded-lg px-2 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                              value={riskSettings.maxPrice}
                              onChange={(e) => setRiskSettings({...riskSettings, maxPrice: e.target.value})}
                            />
                          </div>
                        </div>
                        <div className="grid grid-cols-1 gap-2">
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">SL% Stage</label>
                            <input
                              type="number"
                              className="w-full border-2 border-gray-200 rounded-lg px-2 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                              value={riskSettings.slStage}
                              onChange={(e) => setRiskSettings({...riskSettings, slStage: e.target.value})}
                            />
                          </div>
                        </div>
                      </div>

                      <div>
                        <h4 className="text-sm font-bold text-gray-800 mb-3">Portfolio Settings</h4>
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Portfolio Size</label>
                            <input
                              type="number"
                              className="w-full border-2 border-gray-200 rounded-lg px-2 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                              value={riskSettings.portfolioSize}
                              onChange={(e) => setRiskSettings({...riskSettings, portfolioSize: e.target.value})}
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Max Position (%)</label>
                            <input
                              type="number"
                              className="w-full border-2 border-gray-200 rounded-lg px-2 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                              value={riskSettings.maxPositioning}
                              onChange={(e) => setRiskSettings({...riskSettings, maxPositioning: e.target.value})}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </aside>

        {sidebarOpen && (
          <div
            className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        <main className={`flex-1 min-h-screen transition-all duration-300 ${sidebarVisible ? '' : 'lg:ml-12'}`}>
         <div className="hidden lg:flex items-center justify-between p-6 bg-white/80 backdrop-blur-md border-b border-gray-200/50 sticky top-0 z-30">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">Trading Dashboard</h1>
              <p className="text-sm text-gray-500 mt-1">
                {lastSignalUpdate 
                  ? `Signals updated: ${lastSignalUpdate.toLocaleTimeString()}` 
                  : 'Trading Management System'}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleRefreshSignals}
                disabled={signalsLoading || !token}
                className={`flex items-center space-x-2 px-6 py-3 rounded-xl font-semibold transition-all shadow-lg ${
                  signalsLoading || !token
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white hover:from-blue-600 hover:to-indigo-700'
                }`}
              >
                <svg className={`w-5 h-5 ${signalsLoading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>{signalsLoading ? 'Refreshing...' : 'Refresh Signals'}</span>
              </button>
              <div className="text-sm text-gray-500 bg-gray-100/80 px-4 py-2 rounded-full">
                <span className="font-medium">Real Signals:</span> {realSignals.length}
              </div>
            </div>
          </div>

          {/* Error Message */}
          {signalsError && (
            <div className="mx-6 mt-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center justify-between">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-red-800 font-medium">{signalsError}</p>
              </div>
              <button
                onClick={() => setSignalsError(null)}
                className="text-red-600 hover:text-red-800"
              >
                ×
              </button>
            </div>
          )}

          <div className="px-6 pt-6">
            <BuySignalsTicker signals={signals} setSignals={setSignals} />
          </div>

          <div className="p-6 space-y-6">
            {/* Row 1: Executor (2/3) + Buy in Transit (1/3) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <Executor
                  autoExecutor={autoExecutor}
                  setAutoExecutor={setAutoExecutor}
                  buySignals={signals}
                  onBookBuyFromSignal={handleBookBuyFromSignal}
                  sellSignals={sellSignals}
                  executorLogs={executorLogs}
                  onBookSellFromSignal={handleBookSellFromSignal}
                />
              </div>
              
              <div className="lg:col-span-1">
                <SectionCard
                  number="2"
                  title="Buy in Transit"
                  gradient="from-indigo-500 to-blue-600"
                >
                  <div className="h-full overflow-y-auto space-y-3">
                    {inTransit.length > 0 ? (
                      inTransit.map((order, i) => (
                        <div key={i} className="p-4 bg-gradient-to-br from-indigo-50 to-blue-50 border border-indigo-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-200">
                          <div className="flex justify-between items-start mb-3">
                            <div>
                              <div className="flex items-center mb-2">
                                <span className="font-bold text-indigo-800 text-lg">{order.symbol}</span>
                                <span className="mx-2 text-indigo-600">@</span>
                                <span className="font-mono text-indigo-800 font-semibold">₹{order.exactPrice || order.close}</span>
                              </div>
                              <div className="text-sm text-indigo-700 mb-1">
                                <span className="font-medium">Qty:</span> {order.qty || order.quantity}
                              </div>
                              <div className="text-sm text-indigo-700 mb-1">
                                <span className="font-medium">Amount:</span> ₹{(((order.exactPrice || order.close || 0) * (order.qty || order.quantity || 0)) || 0).toLocaleString()}
                              </div>
                              <div className="text-xs text-indigo-500">
                                Transit: {order.transitDate}
                              </div>
                            </div>
                            <button
                              onClick={() => handleConfirmToRisk(order)}
                              className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 shadow-sm hover:shadow-md flex items-center"
                            >
                              <span className="mr-2">✓</span> Confirm
                            </button>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full text-gray-500">
                        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                          <span className="text-2xl"></span>
                        </div>
                        <p className="text-center">No orders in transit</p>
                      </div>
                    )}
                  </div>
                </SectionCard>
              </div>
            </div>

            {/* Row 2: Risk (2/3) + Sales in Transit (1/3) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <SectionCard
                  number="3"
                  title="Risk"
                  gradient="from-amber-500 to-orange-600"
                >
                  <div className="h-full overflow-y-auto">
                    {risk.length > 0 ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-200">
                              <th className="text-left p-2 font-semibold text-amber-800">Script</th>
                              <th className="text-left p-2 font-semibold text-amber-800">Total Qty</th>
                              <th className="text-left p-2 font-semibold text-amber-800">Av Buy Price</th>
                              <th className="text-left p-2 font-semibold text-amber-800">Amount</th>
                              <th className="text-left p-2 font-semibold text-amber-800">Cl Price</th>
                              <th className="text-left p-2 font-semibold text-amber-800">SL Price</th>
                              <th className="text-left p-2 font-semibold text-amber-800">P&L %</th>
                              <th className="text-left p-2 font-semibold text-amber-800">Status / Action</th>
                            </tr>
                          </thead>
                          <tbody>
                            {risk.map((position, i) => {
                              const plPercent = ((position.clPrice - position.avBuyPrice) / position.avBuyPrice * 100);
                              const isAtRisk = position.clPrice < position.slPrice;
                              const isOddLot = position.quantity >= 1 && position.quantity <= 5;

                              return (
                                <tr key={i} className={`border-b border-amber-100 hover:opacity-90 transition-colors ${
                                  isAtRisk ? 'bg-red-100' : isOddLot ? 'bg-white' : 'bg-green-100'
                                }`}>
                                  <td className="p-2 font-bold text-amber-800">
                                    {position.symbol}
                                    {isOddLot && (
                                      <span className="ml-1 text-xs bg-yellow-100 text-yellow-700 px-1 py-0.5 rounded font-medium">
                                        ODD
                                      </span>
                                    )}
                                  </td>
                                  <td className="p-2 text-amber-700 font-semibold">{position.totalQuantity}</td>
                                  <td className="p-2 text-amber-700 font-mono text-xs">₹{position.avBuyPrice.toFixed(2)}</td>
                                  <td className="p-2 text-amber-700 font-mono text-xs">₹{(position.amount || 0).toLocaleString()}</td>
                                  <td className="p-2 text-amber-700 font-mono text-xs">₹{position.clPrice}</td>
                                  <td className="p-2 text-amber-700 font-mono text-xs">₹{position.slPrice.toFixed(2)}</td>
                                  <td className={`p-2 font-semibold text-xs ${plPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                    {plPercent >= 0 ? '+' : ''}{plPercent.toFixed(2)}%
                                  </td>
                                  <td className="p-2">
                                    {isAtRisk && !isOddLot ? (
                                      <button
                                        onClick={() => handleSellToTransit(position)}
                                        className="bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 text-white px-3 py-1 rounded-lg text-xs font-semibold transition-all duration-200 shadow-sm hover:shadow-md"
                                      >
                                        SELL
                                      </button>
                                    ) : isOddLot ? (
                                      <span className="px-2 py-1 rounded-full text-xs font-bold border bg-yellow-100 text-yellow-700 border-yellow-200">
                                        ODD LOT
                                      </span>
                                    ) : (
                                      <span className="px-2 py-1 rounded-full text-xs font-bold border bg-green-100 text-green-700 border-green-200">
                                        SAFE
                                      </span>
                                    )}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full text-gray-500">
                        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                          <span className="text-2xl"></span>
                        </div>
                        <p className="text-center">No positions at risk</p>
                      </div>
                    )}
                  </div>
                </SectionCard>
              </div>

              <div className="lg:col-span-1">
                <SectionCard
                  number="4"
                  title="Sales in Transit"
                  gradient="from-orange-500 to-red-500"
                >
                  <div className="h-full overflow-y-auto space-y-3">
                    {salesInTransit.length > 0 ? (
                      salesInTransit.map((sale, i) => (
                        <div key={i} className="p-4 bg-gradient-to-br from-orange-50 to-red-50 border border-orange-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-200">
                          <div className="flex justify-between items-start mb-3">
                            <div>
                              <div className="flex items-center mb-2">
                                <span className="font-bold text-orange-800 text-lg">{sale.symbol}</span>
                                <span className="mx-2 text-orange-600">@</span>
                                <span className="font-mono text-orange-800 font-semibold">₹{sale.salePrice.toFixed(2)}</span>
                                {sale.billerId && (
                                  <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full font-medium">
                                    ID: {sale.billerId}
                                  </span>
                                )}
                              </div>
                              <div className="text-sm text-orange-700 mb-1">
                                <span className="font-medium">Qty:</span> {sale.saleQuantity} | <span className="font-medium">{sale.saleReason}</span>
                              </div>
                              <div className="text-sm text-orange-700 mb-1">
                                Expected P&L: ₹{((sale.salePrice - sale.avBuyPrice) * sale.saleQuantity).toFixed(2)}
                              </div>
                              <div className="text-xs text-orange-500">
                                Transit: {sale.transitDate}
                              </div>
                            </div>
                            <button
                              onClick={() => handleSoldConfirm(sale)}
                              className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 shadow-sm hover:shadow-md flex items-center"
                            >
                              <span className="mr-2">✓</span> Sold
                            </button>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full text-gray-500">
                        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                          <span className="text-2xl">💰</span>
                        </div>
                        <p className="text-center">No sales in transit</p>
                      </div>
                    )}
                  </div>
                </SectionCard>
              </div>
            </div>

            {/* Row 3: Balance - Full Width */}
            <div className="grid grid-cols-1 gap-6">
              <SectionCard
                number="5"
                title="Balance"
                gradient="from-blue-600 to-cyan-600"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 rounded-xl shadow-sm">
                    <div className="text-2xl font-bold text-green-700 mb-1">₹{(cashBalance || 0).toLocaleString()}</div>
                    <div className="text-sm font-medium text-green-600">Available Cash</div>
                    <div className="w-full bg-green-100 rounded-full h-2 mt-2">
                      <div
                        className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all duration-500"
                        style={{width: `${((cashBalance || 0) / (parseInt(riskSettings?.portfolioSize || 1000000))) * 100}%`}}
                      ></div>
                    </div>
                  </div>

                  <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl shadow-sm">
                    <div className="text-2xl font-bold text-blue-700 mb-1">₹{((parseInt(riskSettings?.portfolioSize || 1000000) - (cashBalance || 0)) || 0).toLocaleString()}</div>
                    <div className="text-sm font-medium text-blue-600">Risk Amount</div>
                    <div className="w-full bg-blue-100 rounded-full h-2 mt-2">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full transition-all duration-500"
                        style={{width: `${(((parseInt(riskSettings?.portfolioSize || 1000000) - (cashBalance || 0)) / parseInt(riskSettings?.portfolioSize || 1000000)) * 100) || 0}%`}}
                      ></div>
                    </div>
                  </div>

                  <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-indigo-50 border-2 border-purple-200 rounded-xl shadow-sm">
                    <div className={`text-2xl font-bold mb-1 ${(cumulativeProfitLoss || 0) >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                      ₹{(cumulativeProfitLoss || 0).toLocaleString()}
                    </div>
                    <div className="text-sm font-medium text-purple-600">Cumulative P&L</div>
                  </div>

                  <div className="text-center p-4 bg-gradient-to-br from-cyan-50 to-blue-50 border-2 border-cyan-200 rounded-xl shadow-sm">
                    <div className="text-2xl font-bold text-cyan-700 mb-1">
                      ₹{calculatePortfolioValue().toLocaleString()}
                    </div>
                    <div className="text-sm font-medium text-cyan-600">Total Portfolio Value</div>
                    <div className="text-xs text-cyan-500 mt-1">
                      Cash + Risk + Odd Lots + P&L
                    </div>
                  </div>
                </div>

                <OddLotBalance oddLots={oddLots} />
              </SectionCard>
            </div>

            {/* Row 4: Biller - Full Width */}
            <div className="grid grid-cols-1 gap-6">
              <Biller
                billerPositions={billerPositions}
                onSellFromBiller={handleSellFromBiller}
              />
            </div>
          </div>
        </main>
      </div>

      <BookBuyPopup
        signal={selectedSignal}
        isOpen={showBookBuyPopup}
        onClose={() => {
          setShowBookBuyPopup(false);
          setSelectedSignal(null);
        }}
        onConfirm={handleBookBuyConfirm}
        token={token}
      />

      <BookSellPopup
        signal={selectedSignal}
        isOpen={showBookSellPopup}
        onClose={() => {
          setShowBookSellPopup(false);
          setSelectedSignal(null);
        }}
        onConfirm={handleBookSellConfirm}
        token={token}
      />

      {showAddIndustry && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-8 w-full max-w-md shadow-2xl">
            <h3 className="text-xl font-bold text-gray-800 mb-6">Add New Industry</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Industry Name</label>
                <input
                  type="text"
                  value={newIndustry.sector}
                  onChange={(e) => setNewIndustry({...newIndustry, sector: e.target.value})}
                  className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Technology"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Initial Weightage (%)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={newIndustry.weightage}
                  onChange={(e) => setNewIndustry({...newIndustry, weightage: parseInt(e.target.value)})}
                  className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="flex items-center p-4 bg-gray-50 rounded-xl">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={newIndustry.enabled}
                  onChange={(e) => setNewIndustry({...newIndustry, enabled: e.target.checked})}
                  className="mr-3 w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <label htmlFor="enabled" className="text-sm font-medium text-gray-700">Enable by default</label>
              </div>
            </div>
            <div className="flex justify-end space-x-4 mt-8">
              <button
                onClick={() => setShowAddIndustry(false)}
                className="px-6 py-3 text-gray-600 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleAddIndustry}
                className="px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl hover:from-blue-600 hover:to-indigo-700 transition-all duration-200 font-medium shadow-lg hover:shadow-xl"
              >
                Add Industry
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes scroll {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-100%);
          }
        }

        .animate-scroll {
          animation: scroll 30s linear infinite;
        }

        .animate-scroll:hover {
          animation-play-state: paused;
        }

        .scrollbar-thin {
          scrollbar-width: thin;
        }

        .scrollbar-thumb-gray-300::-webkit-scrollbar-thumb {
          background-color: #d1d5db;
          border-radius: 4px;
        }

        .scrollbar-track-gray-100::-webkit-scrollbar-track {
          background-color: #f3f4f6;
          border-radius: 4px;
        }

        .scrollbar-thin::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
      `}</style>
    </div>
  );
}

// ============================================
// MAIN APP
// ============================================

function App() {
  return (
    <AuthProvider>
      <AuthWrapper>
        <TradingDashboard />
      </AuthWrapper>
    </AuthProvider>
  );
}

export default App;