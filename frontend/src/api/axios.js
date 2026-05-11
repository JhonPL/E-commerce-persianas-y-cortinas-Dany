import axios from "axios";
import { API_URL } from "../config/api";

const api = axios.create({

    baseURL: API_URL,
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
                const { data } = await axios.post(`${API_URL}/auth/token/refresh/`, { refreshResponse })

                localStorage.setItem('access_token', data.access)

                requestOriginal.headers['Authorization'] = `Bearer ${data.access}`
                return api(requestOriginal)
            } catch {
        // El refresh token también expiró → cerrar sesión
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('usuario')
        window.location.href = '/'
      }
    }
    return Promise.reject(error)
}
)



export default api