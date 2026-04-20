import React, { useState, useEffect } from 'react';
import { firestore, database } from './firebase/config';
import { ref, onValue, push, set, remove, update } from 'firebase/database';
import { collection, addDoc, query, onSnapshot, deleteDoc, doc, updateDoc } from 'firebase/firestore';
import { Toaster, toast } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  Legend, ResponsiveContainer
} from 'recharts';
import './App.css';

function App() {
  const [logs, setLogs] = useState([]);
  const [registeredCards, setRegisteredCards] = useState([]);
  const [ppePhotos, setPpePhotos] = useState([]);
  const [openPhotoModal, setOpenPhotoModal] = useState(false);
  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [registering, setRegistering] = useState(false);
  const [dateFilter, setDateFilter] = useState('all');
  const [stats, setStats] = useState({
    totalCards: 0,
    activeCards: 0,
    totalAccess: 0,
    approvedAccess: 0,
    rejectedAccess: 0,
    todayAccess: 0,
    weeklyAccess: [],
    ppeComplianceRate: 0
  });

  // Form state
  const [formData, setFormData] = useState({
    uid: '',
    name: '',
    department: '',
    status: 'active'
  });

  // Fetch data from Firebase
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = () => {
    setLoading(true);
    
    // Fetch registered cards from Firestore
    const cardsQuery = query(collection(firestore, 'registered_cards'));
    const unsubscribeCards = onSnapshot(cardsQuery, (snapshot) => {
      const cardsList = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setRegisteredCards(cardsList);
      setStats(prev => ({
        ...prev,
        totalCards: cardsList.length,
        activeCards: cardsList.filter(card => card.status !== 'blocked').length
      }));
    });

    // Fetch access logs with PPE details
    const logsRef = ref(database, 'access_logs');
    const unsubscribeLogs = onValue(logsRef, (snapshot) => {
      const data = snapshot.val();
      if (data) {
        const logsList = Object.keys(data).map(key => ({
          id: key,
          ...data[key]
        })).reverse();
        
        setLogs(logsList);
        
        // Calculate stats
        const today = new Date().toISOString().split('T')[0];
        const todayLogs = logsList.filter(log => log.date === today);
        const approved = logsList.filter(log => log.status === 'PPE_APPROVED');
        const rejected = logsList.filter(log => log.status === 'PPE_REJECTED');
        
        // Calculate weekly data
        const weeklyData = [];
        for (let i = 6; i >= 0; i--) {
          const date = new Date();
          date.setDate(date.getDate() - i);
          const dateStr = date.toISOString().split('T')[0];
          const dayLogs = logsList.filter(log => log.date === dateStr);
          weeklyData.push({
            day: date.toLocaleDateString('en-US', { weekday: 'short' }),
            approved: dayLogs.filter(log => log.status === 'PPE_APPROVED').length,
            rejected: dayLogs.filter(log => log.status === 'PPE_REJECTED').length
          });
        }
        
        const complianceRate = logsList.length > 0 
          ? ((approved.length / logsList.length) * 100).toFixed(1)
          : 0;
        
        setStats(prev => ({
          ...prev,
          totalAccess: logsList.length,
          approvedAccess: approved.length,
          rejectedAccess: rejected.length,
          todayAccess: todayLogs.length,
          weeklyAccess: weeklyData,
          ppeComplianceRate: complianceRate
        }));
      } else {
        setLogs([]);
      }
      setLoading(false);
    });

    // Fetch PPE photos
    const photosRef = ref(database, 'ppe_photos');
    const unsubscribePhotos = onValue(photosRef, (snapshot) => {
      const data = snapshot.val();
      if (data) {
        const photosList = Object.keys(data).map(key => ({
          id: key,
          ...data[key]
        })).reverse();
        setPpePhotos(photosList);
      } else {
        setPpePhotos([]);
      }
    });
    
    // Return unsubscribe functions for cleanup
    return () => {
      unsubscribeCards();
      unsubscribeLogs();
      unsubscribePhotos();
    };
  };

  const handleRegisterCard = async () => {
    console.log('🔴 Register card clicked');
    console.log('📝 Form data:', formData);
    
    if (!formData.uid || !formData.name) {
      console.error('❌ Missing required fields');
      toast.error('❌ Please fill all required fields');
      return;
    }

    console.log('✅ Validation passed, attempting to save...');
    setRegistering(true);
    
    try {
      console.log('⏳ Creating card data...');
      const cardData = {
        uid: formData.uid,
        name: formData.name,
        department: formData.department || 'General',
        registered_date: new Date().toISOString(),
        status: formData.status || 'active'
      };
      console.log('📝 Card data to save:', cardData);
      
      console.log('⏳ Writing to Firestore...');
      const docRef = await addDoc(collection(firestore, 'registered_cards'), cardData);
      
      console.log('✅ Card saved successfully to Firestore!');
      console.log('📝 Document ID:', docRef.id);
      toast.success(`✅ Card registered for ${formData.name}`);
      resetForm();
      setRegistering(false);
      
    } catch (error) {
      console.error('❌ Firestore error:', error);
      console.error('📊 Error details:', {
        message: error.message,
        code: error.code,
        stack: error.stack
      });
      toast.error(`❌ Error registering card: ${error.message}`);
      setRegistering(false);
    }
  };

  const toggleCardStatus = async (cardId, currentStatus) => {
    const newStatus = currentStatus === 'active' ? 'blocked' : 'active';
    try {
      await updateDoc(doc(firestore, 'registered_cards', cardId), { status: newStatus });
      toast.success(`✅ Card ${newStatus === 'active' ? 'activated' : 'blocked'} successfully`);
    } catch (error) {
      console.error('❌ Error updating card status:', error);
      toast.error('❌ Error updating card status');
    }
  };

  const deleteCard = async (cardId, cardName) => {
    if (window.confirm(`Are you sure you want to delete card for ${cardName}?`)) {
      try {
        await deleteDoc(doc(firestore, 'registered_cards', cardId));
        toast.success('✅ Card deleted successfully');
      } catch (error) {
        console.error('❌ Error deleting card:', error);
        toast.error('❌ Error deleting card');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      uid: '',
      name: '',
      department: '',
      status: 'active'
    });
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'PPE_APPROVED': return 'success';
      case 'PPE_REJECTED': return 'error';
      default: return 'warning';
    }
  };

  const getStatusLabel = (status) => {
    switch(status) {
      case 'PPE_APPROVED': return '✓ PPE Passed';
      case 'PPE_REJECTED': return '✗ PPE Failed';
      case 'CARD_ACCEPTED': return '✓ Card Accepted';
      case 'CARD_REJECTED': return '✗ Card Rejected';
      default: return status;
    }
  };

  const filteredLogs = logs.filter(log => {
    const matchesSearch = 
      log.user_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.card_uid?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.status?.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (dateFilter === 'all') return matchesSearch;
    if (dateFilter === 'today') return matchesSearch && log.date === new Date().toISOString().split('T')[0];
    if (dateFilter === 'week') {
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      return matchesSearch && new Date(log.timestamp) >= weekAgo;
    }
    return matchesSearch;
  });

  const filteredCards = registeredCards.filter(card =>
    card.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    card.uid?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    card.department?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Pie chart data
  const pieData = [
    { name: 'PPE Approved', value: stats.approvedAccess, color: '#4caf50' },
    { name: 'PPE Rejected', value: stats.rejectedAccess, color: '#f44336' }
  ];

  return (
    <div className="App">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="header">
        <div className="header-container">
          <div className="header-content">
            <h1 className="header-title">
              🔒 PPE Compliance Dashboard
            </h1>
            <p className="header-subtitle">Telecom Warehouse Access Control System | Real-time Monitoring</p>
          </div>
          <button className="btn-refresh" onClick={fetchData}>
            🔄 Refresh
          </button>
        </div>
      </header>

      <main className="main-content">
        {/* Statistics Cards */}
        <div className="stats-grid">
          <motion.div whileHover={{ scale: 1.02 }} className="stat-card">
            <div className="stat-icon">👥</div>
            <h3>Total Cards</h3>
            <div className="stat-value">{stats.totalCards}</div>
            <p className="stat-subtitle">Active: {stats.activeCards}</p>
          </motion.div>
          
          <motion.div whileHover={{ scale: 1.02 }} className="stat-card">
            <div className="stat-icon">📊</div>
            <h3>Total Access</h3>
            <div className="stat-value">{stats.totalAccess}</div>
            <p className="stat-subtitle">Today: {stats.todayAccess}</p>
          </motion.div>
          
          <motion.div whileHover={{ scale: 1.02 }} className="stat-card stat-card-success">
            <div className="stat-icon">✓</div>
            <h3>PPE Passed</h3>
            <div className="stat-value">{stats.approvedAccess}</div>
            <p className="stat-subtitle">{stats.ppeComplianceRate}% compliance</p>
          </motion.div>
          
          <motion.div whileHover={{ scale: 1.02 }} className="stat-card stat-card-error">
            <div className="stat-icon">✗</div>
            <h3>PPE Failed</h3>
            <div className="stat-value">{stats.rejectedAccess}</div>
            <p className="stat-subtitle">Review required</p>
          </motion.div>
        </div>

        {/* Charts Section */}
        <div className="charts-section">
          <div className="chart-container large">
            <h3 className="chart-title">📈 Weekly Access Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stats.weeklyAccess}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
                <XAxis dataKey="day" stroke="#999" />
                <YAxis stroke="#999" />
                <RechartsTooltip 
                  contentStyle={{ background: 'rgba(255,255,255,0.95)', border: 'none', borderRadius: '8px' }}
                />
                <Legend />
                <Bar dataKey="approved" fill="#4caf50" name="PPE Passed" radius={[8, 8, 0, 0]} />
                <Bar dataKey="rejected" fill="#f44336" name="PPE Failed" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3 className="chart-title">🎯 Overall Compliance</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs-section">
          <div className="tabs">
            <button 
              className={`tab ${tabValue === 0 ? 'active' : ''}`}
              onClick={() => setTabValue(0)}
            >
              📝 Access Logs
            </button>
            <button 
              className={`tab ${tabValue === 1 ? 'active' : ''}`}
              onClick={() => setTabValue(1)}
            >
              📷 PPE Photos
            </button>
            <button 
              className={`tab ${tabValue === 2 ? 'active' : ''}`}
              onClick={() => setTabValue(2)}
            >
              👥 Registered Cards
            </button>
            <button 
              className={`tab ${tabValue === 3 ? 'active' : ''}`}
              onClick={() => setTabValue(3)}
            >
              ➕ Register Card
            </button>
          </div>
        </div>

        {/* Search and Filter */}
        <div className="search-filter">
          <input
            type="text"
            className="search-input"
            placeholder="🔍 Search by name, UID, or status..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {tabValue === 0 && (
            <button
              className="btn-filter"
              onClick={() => setDateFilter(dateFilter === 'all' ? 'today' : 'all')}
            >
              {dateFilter === 'all' ? '📅 Show Today Only' : '📅 Show All'}
            </button>
          )}
        </div>

        {/* Tab 1: Access Logs */}
        {tabValue === 0 && (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>User / Card</th>
                  <th>PPE Detected</th>
                  <th>Missing PPE</th>
                  <th>Status</th>
                  <th>Photo</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="table-row">
                    <td>
                      <strong>{log.time}</strong>
                      <small>{log.date}</small>
                    </td>
                    <td>
                      <strong>{log.user_name || 'Unknown'}</strong>
                      <code>{log.card_uid}</code>
                    </td>
                    <td>
                      <div className="chip-group">
                        {log.ppe_detected && log.ppe_detected.map((item, idx) => (
                          <span key={idx} className="chip chip-success">{item}</span>
                        ))}
                      </div>
                    </td>
                    <td>
                      <div className="chip-group">
                        {log.ppe_missing && log.ppe_missing.length > 0 && log.ppe_missing.map((item, idx) => (
                          <span key={idx} className="chip chip-error">{item}</span>
                        ))}
                      </div>
                    </td>
                    <td>
                      <span className={`status-badge status-${getStatusColor(log.status)}`}>
                        {getStatusLabel(log.status)}
                      </span>
                    </td>
                    <td>
                      {log.image_url && (
                        <button
                          className="btn-icon"
                          onClick={() => {
                            setSelectedPhoto(log);
                            setOpenPhotoModal(true);
                          }}
                        >
                          📷
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredLogs.length === 0 && <p className="no-data">No logs found</p>}
          </div>
        )}

        {/* Tab 2: PPE Photos Gallery */}
        {tabValue === 1 && (
          <div className="gallery-section">
            <h3>📷 PPE Detection Photos Gallery</h3>
            <p className="section-subtitle">Captured images from PPE compliance checks</p>
            
            <div className="gallery-grid">
              {ppePhotos.map((photo) => (
                <motion.div
                  key={photo.id}
                  className="gallery-item"
                  whileHover={{ scale: 1.05 }}
                  onClick={() => {
                    setSelectedPhoto(photo);
                    setOpenPhotoModal(true);
                  }}
                >
                  <img
                    src={photo.image_url || `https://via.placeholder.com/300x300?text=PPE+Photo`}
                    alt={`PPE Check - ${photo.user_name}`}
                  />
                  <div className="gallery-info">
                    <h4>{photo.user_name}</h4>
                    <p>{photo.date} {photo.time}</p>
                    <span className={`status-badge status-${photo.status === 'APPROVED' ? 'success' : 'error'}`}>
                      {photo.status}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
            
            {ppePhotos.length === 0 && (
              <div className="alert alert-info">ℹ️ No PPE photos available yet</div>
            )}
          </div>
        )}

        {/* Tab 3: Registered Cards */}
        {tabValue === 2 && (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Card UID</th>
                  <th>Department</th>
                  <th>Registered Date</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredCards.map((card) => (
                  <tr key={card.id} className="table-row">
                    <td><strong>{card.name}</strong></td>
                    <td><code>{card.uid}</code></td>
                    <td>{card.department}</td>
                    <td>{new Date(card.registered_date).toLocaleDateString()}</td>
                    <td>
                      <span className={`status-badge status-${card.status === 'active' ? 'success' : 'error'}`}>
                        {card.status}
                      </span>
                    </td>
                    <td>
                      <button
                        className={`btn-action ${card.status === 'active' ? 'btn-block' : 'btn-activate'}`}
                        onClick={() => toggleCardStatus(card.id, card.status)}
                        title={card.status === 'active' ? 'Block Card' : 'Activate Card'}
                      >
                        {card.status === 'active' ? '🚫 Block' : '✓ Activate'}
                      </button>
                      <button
                        className="btn-action btn-delete"
                        onClick={() => deleteCard(card.id, card.name)}
                        title="Delete Card"
                      >
                        🗑️ Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredCards.length === 0 && <p className="no-data">No registered cards found</p>}
          </div>
        )}

        {/* Tab 4: Register New Card */}
        {tabValue === 3 && (
          <div className="form-section">
            <h3>Register New RFID Card</h3>
            <p className="section-subtitle">Tap the RFID card on the reader to auto-fill the UID, or enter manually</p>
            
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="uid">Card UID</label>
                <input
                  id="uid"
                  type="text"
                  className="form-input"
                  value={formData.uid}
                  onChange={(e) => setFormData({...formData, uid: e.target.value})}
                  placeholder="e.g., a1b2c3d4"
                />
                <small>Scan the card or enter UID manually</small>
              </div>

              <div className="form-group">
                <label htmlFor="name">Full Name</label>
                <input
                  id="name"
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="John Doe"
                />
              </div>

              <div className="form-group">
                <label htmlFor="department">Department</label>
                <input
                  id="department"
                  type="text"
                  className="form-input"
                  value={formData.department}
                  onChange={(e) => setFormData({...formData, department: e.target.value})}
                  placeholder="Warehouse, Maintenance, Security, etc."
                />
              </div>

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.status === 'active'}
                    onChange={(e) => setFormData({...formData, status: e.target.checked ? 'active' : 'blocked'})}
                  />
                  <span>Card Active (can access facility)</span>
                </label>
              </div>
            </div>
            
            <div className="form-actions">
              <button
                className="btn btn-primary"
                onClick={handleRegisterCard}
                disabled={registering}
                style={{
                  opacity: registering ? 0.7 : 1,
                  cursor: registering ? 'not-allowed' : 'pointer'
                }}
              >
                {registering ? (
                  <>
                    <span className="spinner"></span> Registering...
                  </>
                ) : (
                  <>➕ Register Card</>
                )}
              </button>
              <button 
                className="btn btn-secondary" 
                onClick={resetForm}
                disabled={registering}
              >
                Clear Form
              </button>
            </div>
          </div>
        )}

        {/* Photo Modal */}
        <AnimatePresence>
          {openPhotoModal && selectedPhoto && (
            <motion.div 
              className="modal-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpenPhotoModal(false)}
            >
              <motion.div 
                className="modal-content"
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
              >
                <button 
                  className="btn-close"
                  onClick={() => setOpenPhotoModal(false)}
                >
                  ✕
                </button>
                <img
                  src={selectedPhoto.image_url || `https://via.placeholder.com/800x600?text=PPE+Photo`}
                  alt="PPE Check"
                  className="modal-image"
                />
                <div className="modal-info">
                  <h3>{selectedPhoto.user_name}</h3>
                  <p><strong>Date:</strong> {selectedPhoto.date} {selectedPhoto.time}</p>
                  <p><strong>Status:</strong> {selectedPhoto.status}</p>
                  {selectedPhoto.ppe_detected && (
                    <p><strong>PPE Detected:</strong> {selectedPhoto.ppe_detected.join(', ')}</p>
                  )}
                  {selectedPhoto.ppe_missing && selectedPhoto.ppe_missing.length > 0 && (
                    <p className="text-error"><strong>Missing:</strong> {selectedPhoto.ppe_missing.join(', ')}</p>
                  )}
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Real-time Alert Section */}
        <div className="alert alert-info">
          💡 <strong>Real-time monitoring active:</strong> All access attempts and PPE checks are logged immediately with photos. Blocked cards will be rejected automatically by the system.
        </div>
      </main>
    </div>
  );
}

export default App;