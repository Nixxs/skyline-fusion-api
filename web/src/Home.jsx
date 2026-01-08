import { Box, Typography } from "@mui/material";
import { useRef, useState, useEffect } from "react";

export default function Home() {
  const sgWorldRef = useRef(null);
  const panoRef = useRef(null);
  const panoDivRef = useRef(null);
  const viewshedRef = useRef(null);

  const [connected, setConnected] = useState(false);
  const [params, setParams] = useState(null);

  const [message, setMessage] = useState("");

  // --- Detect SGWorld (your existing logic) ---
  useEffect(() => {
    let cancelled = false;

    function waitForFusion() {
      try {
        const parentWin = window.parent || window;

        if (
          parentWin &&
          parentWin.SGWorld &&
          parentWin.SGWorld.Creator
        ) {
          sgWorldRef.current = parentWin.SGWorld;
          setConnected(true);
          console.log("✅ Connected to Fusion SGWorld");
          return;
        }

        try {
            if (typeof __sgworld__!=="undefined") {
                sgWorldRef.current =__sgworld__.SetParamEx(9970,80);
                setConnected(true);
                console.log("✅ Connected to TEPro SGWorld");

                const urlParams = getQueryParams();

                let postion = sgWorldRef.current.Creator.CreatePosition(
                    urlParams.lng,
                    urlParams.lat,
                    20,
                    0,
                    0,
                    0,
                    0,
                    300
                );

                viewshedRef.current = sgWorldRef.current.Analysis.Create3DViewshed(
                    postion,
                    120,
                    120,
                    100,
                    "",
                    "Street View"
                );
            }
        } catch(e) {
            console.log(e);
            alert(e);
        }

        return null;
      } catch (err) {
        console.warn("Error accessing parent.SGWorld:", err);
      }

      if (!cancelled) setTimeout(waitForFusion, 200);
    }

    waitForFusion();
    return () => { cancelled = true; };
  }, []);

  // --- Parse URL params once ---
  useEffect(() => {
    const p = getQueryParams();
    if (!p) {
      console.warn("No valid lat/lng in URL");
      return;
    }
    setParams(p);
  }, []);

  // --- Init Street View ---
  useEffect(() => {
    if (!params) return;

    loadGoogleMaps(import.meta.env.VITE_GOOGLE_MAPS_KEY)
      .then(() => {
        panoRef.current = new window.google.maps.StreetViewPanorama(
          panoDivRef.current,
          {
            position: { lat: params.lat, lng: params.lng },
            pov: {
              heading: params.heading,
              pitch: params.pitch
            },
            zoom: params.zoom,
            disableDefaultUI: true,
            showRoadLabels: false
          }
        );

        // --- Camera direction listener ---
        panoRef.current.addListener("pov_changed", () => {
          const pov = panoRef.current.getPov();
          const zoom = panoRef.current.getZoom();

          const payload = {
            heading: pov.heading,
            pitch: pov.pitch,
            zoom
          };

          console.log("📷 POV changed", payload);

          // OPTIONAL: push back into TerraExplorer
          if (sgWorldRef.current) {
            try {
              let posX = viewshedRef.current.Position.X;
              let posY = viewshedRef.current.Position.Y;

              viewshedRef.current.Position.Yaw = pov.heading;
              setMessage(`x: ${posX} y: ${posY} heading: ${pov.heading}`);
              
            } catch (err) {
              console.warn("Failed to send POV to SGWorld", err);
              alert("error happened");
            }
          }
        });
      })
      .catch(err => {
        console.error("Failed to load Google Maps", err);
      });
  }, [params]);

  return (
    <Box sx={{ width: "100vw", height: "100vh" }}>
      {!params && (
        <Typography sx={{ p: 2 }}>
          No valid Street View coordinates provided.
        </Typography>
      )}
      <Box>
        <Typography>
            Log Message: {message}
        </Typography>
      </Box>
      <Box
        ref={panoDivRef}
        sx={{
          width: "100%",
          height: "100%",
          background: "black"
        }}
      />
    </Box>
  );
}

/* ---------------- helpers ---------------- */

function getQueryParams() {
  const params = new URLSearchParams(window.location.search);

  const lat = parseFloat(params.get("lat"));
  const lng = parseFloat(params.get("lng"));

  if (Number.isNaN(lat) || Number.isNaN(lng)) return null;

  return {
    lat,
    lng,
    heading: parseFloat(params.get("heading")) || 0,
    pitch: parseFloat(params.get("pitch")) || 0,
    zoom: parseFloat(params.get("zoom")) || 1
  };
}

function loadGoogleMaps(apiKey) {
  if (window.google?.maps) return Promise.resolve();

  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}`;
    script.async = true;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}
