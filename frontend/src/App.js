// frontend/src/App.js
import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a resume file.');
      return;
    }

    setLoading(true);
    setError(null);
    setAnalysisResult(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post('http://localhost:5000/analyze/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setAnalysisResult(response.data);
    } catch (err) {
      console.error('Error uploading resume:', err);
      setError('Failed to upload and analyze the resume. Please try again.');
      if (err.response) {
        console.error('Backend error:', err.response.data);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h1>Resume Analyzer</h1>
      <div className="upload-section">
        <input type="file" accept=".pdf" onChange={handleFileChange} />
        <button onClick={handleUpload} disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze Resume'}
        </button>
        {error && <p className="error-message">{error}</p>}
      </div>

      {analysisResult && (
        <div className="results-section">
          <h2>Analysis Results</h2>
          {analysisResult.extracted_text && (
            <div className="extracted-text">
              <h3>Extracted Text</h3>
              <pre>{analysisResult.extracted_text}</pre>
            </div>
          )}

          {analysisResult.analysis && (
            <div className="key-sections-analysis">
              <h3>Key Sections Analysis</h3>
              <p>Education Present: {analysisResult.analysis.key_sections.education_present ? 'Yes' : 'No'}</p>
              <p>Experience Present: {analysisResult.analysis.key_sections.experience_present ? 'Yes' : 'No'}</p>
              <p>Skills Present: {analysisResult.analysis.key_sections.skills_present ? 'Yes' : 'No'}</p>
            </div>
          )}

          {analysisResult.improvement_suggestions && analysisResult.improvement_suggestions.length > 0 && (
            <div className="improvement-suggestions">
              <h3>Improvement Suggestions</h3>
              <ul>
                {analysisResult.improvement_suggestions.map((suggestion, index) => (
                  <li key={index}>{suggestion.suggestion}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;