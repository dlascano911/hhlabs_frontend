// Configuración del bucket S3 - Google Cloud Storage
export const s3Config = {
  bucketUrl: 'https://storage.googleapis.com/handheldlabs-storage/portable-locker',
  images: {
    deviceImage: 'verba-device.png'
  }
}

// Helper para obtener URL completa de un asset
export const getAssetUrl = (assetName) => {
  return `${s3Config.bucketUrl}/${assetName}`
}

// URLs de assets específicos
export const ASSETS = {
  DEVICE_IMAGE: getAssetUrl(s3Config.images.deviceImage)
}
