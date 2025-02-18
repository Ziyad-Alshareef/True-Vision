import UploadArea from '../components/UploadArea';
import '../app.css';
import api from "../api";
import Layout from '../components/Layout';

const Home = () => {
    const handleUpload = async (file) => {
      const formData = new FormData();
      formData.append('video', file);
      
      try {
        const response = await api.post('/api/detect/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        // Handle the response data
        console.log(response.data);
      } catch (error) {
        console.error('Error:', error);
      }
    };
  
    return (
      <div className="max-w-4xl mx-auto py-12">
        <h1 className="text-4xl font-bold mb-2">Welcome to True Vision</h1>
        <p className="text-gray-400 mb-8">Detect the fake, defend the real</p>
        
        <UploadArea onUpload={handleUpload} />
        
        <div className="grid grid-cols-3 gap-8 mt-12">
          <div className="text-center">
            <div className="text-green-500 mb-4">
              {/* Icon */}
            </div>
            <h3 className="font-semibold mb-2">Accurate Detection</h3>
            <p className="text-gray-400">Ensuring precise identification of manipulated content.</p>
          </div>
          {/* Similar feature blocks */}
        </div>
      </div>
    );
  };
  
  export default Home;