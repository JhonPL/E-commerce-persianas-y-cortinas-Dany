import axios  from "axios";

const api = axios.create({

    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },

});


api.interceptors.request.use(config => {

    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }

    return config;

})


api.interceptors.response.use (

    (response) => response,

    async (error) => {
        const requestOriginal = error.config

        if (error.response && error.response.status === 401 && !requestOriginal._retry) {

            requestOriginal._retry = true

            try {
                const refreshResponse = localStorage.getItem('refresh_token')
                const {data} = await axios.post('http://127.0.0.1:8000/api/v1/auth/token/refresh/', {refreshResponse})

                localStorage.setItem('access_token', data.access)

                requestOriginal.headers['Authorization'] = `Bearer ${data.access}`
                return api(requestOriginal)
            } catch {
        // El refresh token también expiró → cerrar sesión
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('usuario')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
}
)



export default api