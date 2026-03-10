import React, { useState } from "react";
import { FaSearch, FaUser, FaShoppingCart } from "react-icons/fa";
import "./App.css";
import useParallax from "./hooks/useParallax";

function App() {
  useParallax();

  const [showSearch, setShowSearch] = useState(false);
  const [query, setQuery] = useState("")

  const productos = [
    { id: 1, nombre: "Cortina Clásica" },
    { id: 2, nombre: "Persiana Enrollable" },
    { id: 3, nombre: "Panel Japonés" },
  ];

  // Filtrar coincidencias
  const resultados = productos.filter((p) =>
    p.nombre.toLowerCase().includes(query.toLowerCase())
  );


  return (
    <>
      <header className="navbar">
        {/* Logo */}
        <div className="logo">
          <a href="#">
            <div>
              <img src="/img/logo dany.png" alt="Logo" />
            </div>
          </a>
        </div>

        {/* Icono búsqueda */}
        <div className="search-box" onClick={() => setShowSearch(true)}>
          <FaSearch />
        </div>

        {/* Menú */}
        <nav className="menu">
          <a href="#inicio">Inicio</a>
          <a href="#tienda">Tienda</a>
          <a href="#contacto">Contacto</a>
        </nav>

        {/* Usuario + Carrito */}
        <div className="user-cart">
          <a href="#"><FaUser /> Entrar</a>
          <a href="#"><FaShoppingCart /></a>
        </div>
      </header>

      <main>
        {/* Hero con parallax */}
        <section id="inicio" className="hero">
          <div className="hero-text">
            <h1 class="titulo">TRANSFORMA</h1>
            <h1 class="titulo">TU HOGAR</h1>
            <p class="subtitulo">¡con estilo¡</p>
          </div>
        </section>

        {/* Productos */}
        <section id="tienda" className="contenedor productos">
          <h1>Nuestros Productos</h1>
          <div className="grid">
            <div className="card">
              <img src="/img/1.jpg" alt="Producto 1" />
              <h3>Cortina Clásica</h3>
              <p>$120.000</p>
            </div>
            <div className="card">
              <img src="/img/2.jpg" alt="Producto 2" />
              <h3>Persiana Enrollable</h3>
              <p>$180.000</p>
            </div>
            <div className="card">
              <img src="/img/3.jpg" alt="Producto 3" />
              <h3>Panel Japonés</h3>
              <p>$250.000</p>
            </div>
          </div>
        </section>

        {/* Imagen parallax entre secciones */}
        <div className="parallax parallax-1"></div>

        {/* Contacto */}
        <section id="contacto" className="contacto">
          <h1>Contáctanos</h1>
          <form>
            <input type="text" placeholder="Nombre" />
            <input type="email" placeholder="Email" />
            <textarea placeholder="Mensaje"></textarea>
            <input type="submit" value="Enviar" />
          </form>
        </section>

        {/* Otra imagen parallax */}
        <div className="parallax parallax-2"></div>
      </main>

      <footer className="footer">
        <div className="back-to-top" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
          <img src="/img/flecha.jpg" alt="Arriba" className="arrow-img" />
          <span className="text">Arriba</span>
        </div>
        <div className="link-env-o-y">Envío y devoluciones</div>
        <div className="link-t-rminos-y">Términos y condiciones</div>
        <div className="list-barra-de-redes">
          <div className="item-link-facebook"></div>
          <div className="item-link-pinterest"></div>
          <div className="item-link-instagram"></div>
        </div>
      </footer>
    </>
  );
}

export default App;
